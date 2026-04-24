"""
agent_runner.py — Runs a single agentic role via Claude Code CLI.

Each call is isolated: the agent sees only the filesystem at wiki_root
and the prompt for its role. No context is shared between calls.

Usage:
    from agent_runner import run_agent, ROLES
    result = run_agent("heartbeat", wiki_root, model="claude-sonnet-4-6")
"""

import json
import subprocess
import time
from pathlib import Path

from rich.console import Console
from rich.text import Text

console = Console(highlight=False)

# Claude CLI — use .cmd on Windows to ensure PATH resolution
import sys, os
CLAUDE_CMD = "claude.cmd" if sys.platform == "win32" else "claude"

# ── role configuration ────────────────────────────────────────────────────────

ROLES = {
    "heartbeat": {
        "prompt_file": "schema/PROMPT-CHECK-SOURCES.md",
        "label": "HB",
        "color": "cyan",
        "timeout": 600,
    },
    "builder": {
        "prompt_file": "schema/PROMPT-BUILD.md",
        "label": "BUILD",
        "color": "yellow",
        "timeout": 1800,
    },
    "reviewer": {
        "prompt_file": "schema/PROMPT-CONTROL.md",
        "label": "REVIEW",
        "color": "blue",
        "timeout": 900,
    },
    "evaluator": {
        "prompt_file": "schema/PROMPT-EVAL.md",
        "label": "EVAL",
        "color": "magenta",
        "timeout": 900,
    },
}

ALLOWED_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep"]


# ── prompt loader ─────────────────────────────────────────────────────────────

def load_prompt(role, wiki_root):
    """
    Load the prompt template for the role from the wiki schema,
    replacing {VAULT_ROOT} with the actual wiki_root path.
    """
    schema_root = Path(wiki_root)
    prompt_path = schema_root / ROLES[role]["prompt_file"]
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    raw = prompt_path.read_text(encoding="utf-8")

    # Extract the prompt body from the markdown code block
    # Prompt files have format:
    #   # PROMPT-X.md
    #   > description
    #   ```text
    #   <actual prompt>
    #   ```
    import re
    m = re.search(r'```text\s*\n(.*?)```', raw, re.DOTALL)
    if m:
        prompt_body = m.group(1).strip()
    else:
        # fallback: use the whole file
        prompt_body = raw.strip()

    # Inject ROOT_PATH
    wiki_root_str = str(Path(wiki_root).resolve()).replace("\\", "/")
    prompt_body = prompt_body.replace('"{VAULT_ROOT}"', f'"{wiki_root_str}"')
    prompt_body = prompt_body.replace("{VAULT_ROOT}", wiki_root_str)

    return prompt_body


# ── runner ────────────────────────────────────────────────────────────────────

def run_agent(role, wiki_root, model="claude-sonnet-4-6", verbose=False):
    """
    Run a single agentic role against wiki_root using the Claude Code CLI.

    Returns a dict:
        role          str
        success       bool
        result        str   (agent's final output text)
        duration_s    float
        cost_usd      float
        num_turns     int
        error         str or None
    """
    cfg = ROLES.get(role)
    if not cfg:
        raise ValueError(f"Unknown role: {role}. Valid: {list(ROLES)}")

    label = cfg["label"]
    color = cfg["color"]
    timeout = cfg["timeout"]

    try:
        prompt = load_prompt(role, wiki_root)
    except FileNotFoundError as e:
        return _error_result(role, str(e), 0)

    wiki_root_abs = str(Path(wiki_root).resolve())

    cmd = [
        CLAUDE_CMD,
        "-p", prompt,
        "--allowedTools", "Write(*) Edit(*) Read(*) Glob(*) Grep(*)",
        "--output-format", "json",
        "--model", model,
        "--permission-mode", "bypassPermissions",
        "--no-session-persistence",
        "--add-dir", wiki_root_abs,
    ]

    # display
    _print_start(label, color)
    t0 = time.time()

    with console.status(
        Text(f"  [{label}] running...", style=f"bold {color}"),
        spinner="dots",
    ):
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(Path(wiki_root).resolve()),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                input="y\n" * 20,  # auto-approve any permission prompts
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            _print_result(label, color, "TIMEOUT", elapsed, 0, 0)
            return _error_result(role, f"Timeout after {timeout}s", elapsed)
        except FileNotFoundError:
            elapsed = time.time() - t0
            _print_result(label, color, "ERROR", elapsed, 0, 0)
            return _error_result(role, f"{CLAUDE_CMD} not found. Is Claude Code installed and in PATH?", elapsed)

    elapsed = time.time() - t0

    # parse JSON output
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        # non-JSON output — treat stdout as plain result
        data = {
            "result": proc.stdout,
            "is_error": proc.returncode != 0,
            "duration_ms": int(elapsed * 1000),
            "total_cost_usd": 0,
            "num_turns": 0,
        }

    success = not data.get("is_error", False) and proc.returncode == 0
    result_text = data.get("result", "")
    cost = data.get("total_cost_usd", 0)
    num_turns = data.get("num_turns", 0)

    # extract summary line from result for display
    summary = _extract_summary(result_text, role)
    status = "OK" if success else "FAIL"
    _print_result(label, color, status, elapsed, cost, num_turns, summary)

    if verbose and result_text:
        console.print(f"    [dim]{result_text[:300]}[/dim]")

    return {
        "role": role,
        "success": success,
        "result": result_text,
        "duration_s": round(elapsed, 1),
        "cost_usd": round(cost, 6),
        "num_turns": num_turns,
        "error": None if success else data.get("api_error_status") or proc.stderr[:200],
    }


# ── display helpers ───────────────────────────────────────────────────────────

def _print_start(label, color):
    console.print(f"  [{color}][{label:6s}][/{color}]", end="  ")


def _print_result(label, color, status, elapsed, cost, turns, summary=""):
    status_style = "green" if status == "OK" else "red" if status in ("FAIL", "ERROR", "TIMEOUT") else "yellow"
    parts = [
        f"[{status_style}]{status}[/{status_style}]",
        f"[dim]{elapsed:.0f}s[/dim]",
    ]
    if cost:
        parts.append(f"[dim]${cost:.4f}[/dim]")
    if turns:
        parts.append(f"[dim]{turns}t[/dim]")
    if summary:
        parts.append(f"[dim]| {summary}[/dim]")
    console.print("  ".join(parts))


def _extract_summary(result_text, role):
    """Extract a short summary line from the agent's return payload."""
    if not result_text:
        return ""
    lines = result_text.strip().splitlines()

    # look for key result lines by role
    keywords = {
        "heartbeat": ["manifests created", "sources detected", "no-op"],
        "builder":   ["pages created", "pages updated", "no-op", "requests resolved"],
        "reviewer":  ["pass", "fail", "corrections applied", "requests emitted"],
        "evaluator": ["status", "pass", "fail", "requests"],
    }
    targets = keywords.get(role, [])
    for line in lines:
        ll = line.lower()
        if any(k in ll for k in targets):
            # clean markdown bold markers
            clean = line.strip().lstrip("- *#").strip()
            return clean[:80]
    # fallback: first non-empty line
    for line in lines:
        if line.strip():
            return line.strip()[:80]
    return ""


def _error_result(role, error_msg, elapsed):
    return {
        "role": role,
        "success": False,
        "result": "",
        "duration_s": round(elapsed, 1),
        "cost_usd": 0,
        "num_turns": 0,
        "error": error_msg,
    }


# ── quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a single agent role.")
    parser.add_argument("role", choices=list(ROLES), help="Role to run")
    parser.add_argument("wiki_root", help="Path to wiki root")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    console.rule(f"[bold]agent_runner test - {args.role}[/bold]")
    result = run_agent(args.role, args.wiki_root, args.model, args.verbose)
    console.rule("[bold]result[/bold]")
    console.print_json(json.dumps(result, indent=2))
