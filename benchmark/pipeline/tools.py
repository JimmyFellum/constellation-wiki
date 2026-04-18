"""
tools.py — Filesystem tools for Constellation Wiki agentic pipeline.

Provides:
- TOOL_DEFINITIONS: list of Anthropic tool schemas to pass to the API
- execute_tool(name, inputs, root_path): executes a tool call locally

All paths are resolved relative to root_path.
Agents cannot read or write outside root_path (path traversal blocked).
"""

import os
import re
import json
from pathlib import Path


# ── security ──────────────────────────────────────────────────────────────────

def safe_path(root_path, relative_path):
    """
    Resolve relative_path against root_path and verify it stays inside.
    Returns resolved absolute Path or raises ValueError.
    """
    root = Path(root_path).resolve()
    target = (root / relative_path).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError(f"Path escape blocked: {relative_path!r} resolves outside root.")
    return target


# ── tool implementations ──────────────────────────────────────────────────────

def _read_file(root_path, path):
    try:
        p = safe_path(root_path, path)
        if not p.exists():
            return {"error": f"File not found: {path}"}
        if not p.is_file():
            return {"error": f"Not a file: {path}"}
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        return {
            "path": path,
            "content": content,
            "line_count": len(lines),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Read failed: {e}"}


def _write_file(root_path, path, content):
    try:
        p = safe_path(root_path, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"path": path, "written": True, "bytes": len(content.encode("utf-8"))}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Write failed: {e}"}


def _edit_file(root_path, path, old_string, new_string, replace_all=False):
    try:
        p = safe_path(root_path, path)
        if not p.exists():
            return {"error": f"File not found: {path}"}
        content = p.read_text(encoding="utf-8")
        if old_string not in content:
            return {"error": f"old_string not found in {path}"}
        count = content.count(old_string)
        if not replace_all and count > 1:
            return {
                "error": (
                    f"old_string appears {count} times in {path}. "
                    "Provide more context to make it unique, or set replace_all=true."
                )
            }
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacements = count
        else:
            new_content = content.replace(old_string, new_string, 1)
            replacements = 1
        p.write_text(new_content, encoding="utf-8")
        return {"path": path, "replacements": replacements}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Edit failed: {e}"}


def _list_directory(root_path, path="."):
    try:
        p = safe_path(root_path, path)
        if not p.exists():
            return {"error": f"Directory not found: {path}"}
        if not p.is_dir():
            return {"error": f"Not a directory: {path}"}
        entries = []
        for item in sorted(p.iterdir()):
            rel = str(item.relative_to(Path(root_path).resolve()))
            rel = rel.replace("\\", "/")
            entries.append({
                "name": item.name,
                "path": rel,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"path": path, "entries": entries, "count": len(entries)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"List failed: {e}"}


def _search_files(root_path, pattern, path=".", file_glob="*.md"):
    """Search for a regex pattern in files matching file_glob under path."""
    try:
        base = safe_path(root_path, path)
        if not base.exists():
            return {"error": f"Path not found: {path}"}
        matches = []
        for f in sorted(base.rglob(file_glob)):
            try:
                text = f.read_text(encoding="utf-8")
                lines = text.splitlines()
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        rel = str(f.relative_to(Path(root_path).resolve()))
                        rel = rel.replace("\\", "/")
                        matches.append({
                            "file": rel,
                            "line": i,
                            "text": line.strip(),
                        })
            except Exception:
                pass
        return {
            "pattern": pattern,
            "file_glob": file_glob,
            "match_count": len(matches),
            "matches": matches[:100],  # cap at 100 to avoid context overflow
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Search failed: {e}"}


def _glob_files(root_path, pattern, path="."):
    """Find files matching a glob pattern."""
    try:
        base = safe_path(root_path, path)
        if not base.exists():
            return {"error": f"Path not found: {path}"}
        found = []
        for f in sorted(base.rglob(pattern)):
            if f.is_file():
                rel = str(f.relative_to(Path(root_path).resolve()))
                rel = rel.replace("\\", "/")
                found.append(rel)
        return {"pattern": pattern, "count": len(found), "files": found}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Glob failed: {e}"}


# ── dispatcher ────────────────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "read_file":      lambda root, inp: _read_file(root, inp["path"]),
    "write_file":     lambda root, inp: _write_file(root, inp["path"], inp["content"]),
    "edit_file":      lambda root, inp: _edit_file(
                          root, inp["path"], inp["old_string"], inp["new_string"],
                          inp.get("replace_all", False)
                      ),
    "list_directory": lambda root, inp: _list_directory(root, inp.get("path", ".")),
    "search_files":   lambda root, inp: _search_files(
                          root, inp["pattern"],
                          inp.get("path", "."),
                          inp.get("file_glob", "*.md")
                      ),
    "glob_files":     lambda root, inp: _glob_files(
                          root, inp["pattern"], inp.get("path", ".")
                      ),
}


def execute_tool(name, inputs, root_path):
    """
    Execute a tool by name with given inputs against root_path.
    Returns a JSON-serializable dict.
    """
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    return handler(root_path, inputs)


# ── Anthropic tool definitions ────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": (
            "Read the full content of a file. "
            "Path must be relative to the wiki root."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file (e.g. 'schema/RULES.md')."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": (
            "Write content to a file, creating it and any parent directories if needed. "
            "Overwrites existing content. "
            "Path must be relative to the wiki root."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to write to."
                },
                "content": {
                    "type": "string",
                    "description": "Full content to write."
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": (
            "Replace a specific string in a file with a new string. "
            "The old_string must appear exactly once unless replace_all is true. "
            "Path must be relative to the wiki root."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file."
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact string to find and replace."
                },
                "new_string": {
                    "type": "string",
                    "description": "String to replace it with."
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "If true, replace all occurrences. Default false.",
                    "default": False
                }
            },
            "required": ["path", "old_string", "new_string"]
        }
    },
    {
        "name": "list_directory",
        "description": (
            "List files and subdirectories in a directory. "
            "Path must be relative to the wiki root."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the directory. Defaults to root.",
                    "default": "."
                }
            },
            "required": []
        }
    },
    {
        "name": "search_files",
        "description": (
            "Search for a regex pattern in files under a given path. "
            "Returns matching lines with file and line number. "
            "Capped at 100 matches."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for."
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in. Defaults to root.",
                    "default": "."
                },
                "file_glob": {
                    "type": "string",
                    "description": "File pattern to filter. Default '*.md'.",
                    "default": "*.md"
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "glob_files",
        "description": (
            "Find files matching a glob pattern under a given path. "
            "Returns a list of relative file paths."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g. 'sources/source-*.md', '**/*.md')."
                },
                "path": {
                    "type": "string",
                    "description": "Base directory to search in. Defaults to root.",
                    "default": "."
                }
            },
            "required": ["pattern"]
        }
    },
]


# ── self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile, shutil

    print("Running tools self-test...")
    tmp = tempfile.mkdtemp()
    try:
        # write
        r = execute_tool("write_file", {"path": "test/hello.md", "content": "# Hello\nworld"}, tmp)
        assert r["written"], f"write failed: {r}"
        print("  write_file         OK")

        # read
        r = execute_tool("read_file", {"path": "test/hello.md"}, tmp)
        assert r["content"] == "# Hello\nworld", f"read failed: {r}"
        print("  read_file          OK")

        # list
        r = execute_tool("list_directory", {"path": "test"}, tmp)
        assert r["count"] == 1, f"list failed: {r}"
        print("  list_directory     OK")

        # edit
        r = execute_tool("edit_file", {"path": "test/hello.md", "old_string": "world", "new_string": "universe"}, tmp)
        assert r["replacements"] == 1, f"edit failed: {r}"
        r = execute_tool("read_file", {"path": "test/hello.md"}, tmp)
        assert "universe" in r["content"], f"edit verify failed: {r}"
        print("  edit_file          OK")

        # glob
        r = execute_tool("glob_files", {"pattern": "**/*.md"}, tmp)
        assert r["count"] == 1, f"glob failed: {r}"
        print("  glob_files         OK")

        # search
        r = execute_tool("search_files", {"pattern": "universe"}, tmp)
        assert r["match_count"] == 1, f"search failed: {r}"
        print("  search_files       OK")

        # path escape blocked
        r = execute_tool("read_file", {"path": "../../etc/passwd"}, tmp)
        assert "error" in r, f"escape not blocked: {r}"
        print("  path escape block  OK")

        print("\nAll tests passed.")
    finally:
        shutil.rmtree(tmp)
