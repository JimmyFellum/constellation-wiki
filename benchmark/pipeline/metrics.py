"""
metrics.py — Constellation Wiki benchmark metrics extractor.
Extracts quantitative and qualitative metrics from a wiki run directory.
Usage: python metrics.py <wiki_root> [--run-id <id>] [--output <path>]
"""

import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone


# ── helpers ──────────────────────────────────────────────────────────────────

def read_frontmatter(path):
    """Extract YAML frontmatter fields from a markdown file (simple parser)."""
    fields = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
        if not text.startswith("---"):
            return fields
        end = text.find("---", 3)
        if end == -1:
            return fields
        fm = text[3:end]
        # parse key: value lines
        for line in fm.splitlines():
            m = re.match(r'^(\w[\w_]*):\s*(.*)', line)
            if m:
                fields[m.group(1)] = m.group(2).strip()
        # parse sources list
        sources = []
        in_sources = False
        for line in fm.splitlines():
            if re.match(r'^sources:', line):
                in_sources = True
                continue
            if in_sources:
                m = re.match(r'^\s+-\s+source_id:\s*(\S+)', line)
                if m:
                    sources.append(m.group(1))
                elif re.match(r'^\w', line):
                    in_sources = False
        if sources:
            fields['_sources_list'] = sources
        # parse relations list
        relations = []
        in_relations = False
        for line in fm.splitlines():
            if re.match(r'^relations:', line):
                in_relations = True
                continue
            if in_relations:
                m = re.match(r'^\s+-\s+type:\s*(\S+)', line)
                if m:
                    relations.append(m.group(1))
                elif re.match(r'^\w', line):
                    in_relations = False
        if relations:
            fields['_relations_list'] = relations
    except Exception:
        pass
    return fields


def count_lines(path):
    try:
        return len(Path(path).read_text(encoding="utf-8").splitlines())
    except Exception:
        return 0


# ── page metrics ─────────────────────────────────────────────────────────────

def collect_pages(wiki_root):
    """Return list of dicts, one per generated knowledge page."""
    pages = []
    for layer in ["entities", "concepts", "playbooks", "synthesis"]:
        layer_path = Path(wiki_root) / layer
        if not layer_path.exists():
            continue
        for md in layer_path.rglob("*.md"):
            fm = read_frontmatter(md)
            page_type = fm.get("type", layer.rstrip("s"))
            sources = fm.get("_sources_list", [])
            relations = fm.get("_relations_list", [])
            pages.append({
                "path": str(md.relative_to(wiki_root)),
                "type": page_type,
                "lines": count_lines(md),
                "source_count": len(sources),
                "sources": sources,
                "relation_count": len(relations),
                "relations": relations,
            })
    return pages


def page_metrics(pages):
    if not pages:
        return {}
    by_type = {}
    for p in pages:
        t = p["type"]
        by_type[t] = by_type.get(t, 0) + 1

    lengths = [p["lines"] for p in pages]
    relations = [p["relation_count"] for p in pages]
    multi_source = [p for p in pages if p["source_count"] > 1]

    return {
        "page_count": len(pages),
        "page_count_by_type": by_type,
        "mean_page_length": round(sum(lengths) / len(lengths), 1),
        "min_page_length": min(lengths),
        "max_page_length": max(lengths),
        "multi_source_pages": len(multi_source),
        "multi_source_pages_pct": round(len(multi_source) / len(pages) * 100, 1),
        "synthesis_ratio": round(by_type.get("synthesis", 0) / len(pages), 3),
    }


# ── graph quality metrics ─────────────────────────────────────────────────────

def parse_relations_from_text(text):
    """Parse all (type, target) relation pairs from frontmatter text."""
    pairs = []
    # match blocks like:  - type: foo\n    target: bar
    for m in re.finditer(r'-\s+type:\s*(\S+)\s*\n\s+target:\s*(\S+)', text):
        pairs.append((m.group(1).strip(), m.group(2).strip()))
    return pairs


def normalize_path(p):
    """Normalize a page path: forward slashes, no .md extension."""
    return p.replace("\\", "/").replace(".md", "")


def graph_metrics(pages, wiki_root):
    """Relation graph quality: density, coverage, bidirectionality, orphans."""

    # generated_from coverage
    total_source_refs = 0
    covered_source_refs = 0
    for p in pages:
        md_path = Path(wiki_root) / p["path"]
        try:
            text = md_path.read_text(encoding="utf-8")
            relations = parse_relations_from_text(text)
            gf_targets = {tgt for rtype, tgt in relations if rtype == "generated_from"}
            for sid in p["sources"]:
                total_source_refs += 1
                logical = sid.replace("src-", "")
                expected = f"sources/source-{logical}"
                if expected in gf_targets:
                    covered_source_refs += 1
        except Exception:
            pass

    generated_from_coverage = (
        round(covered_source_refs / total_source_refs, 3)
        if total_source_refs > 0 else 1.0
    )

    # bidirectionality: check part_of / contains pairs
    part_of_pairs = set()
    contains_pairs = set()
    for p in pages:
        page_key = normalize_path(p["path"])
        md_path = Path(wiki_root) / p["path"]
        try:
            text = md_path.read_text(encoding="utf-8")
            for rtype, tgt in parse_relations_from_text(text):
                tgt_norm = normalize_path(tgt)
                if rtype == "part_of":
                    part_of_pairs.add((page_key, tgt_norm))
                elif rtype == "contains":
                    contains_pairs.add((page_key, tgt_norm))
        except Exception:
            pass

    bidirectional = 0
    total_part_of = len(part_of_pairs)
    for (src, tgt) in part_of_pairs:
        if (tgt, src) in contains_pairs:
            bidirectional += 1
    bidirectional_rate = (
        round(bidirectional / total_part_of, 3)
        if total_part_of > 0 else 1.0
    )

    # orphan pages: pages with no incoming relations
    all_targets = set()
    for p in pages:
        md_path = Path(wiki_root) / p["path"]
        try:
            text = md_path.read_text(encoding="utf-8")
            for _, tgt in parse_relations_from_text(text):
                all_targets.add(normalize_path(tgt))
        except Exception:
            pass

    orphans = []
    for p in pages:
        page_key = normalize_path(p["path"])
        if page_key not in all_targets:
            orphans.append(normalize_path(p["path"]))

    total_relations = sum(p["relation_count"] for p in pages)
    relation_density = (
        round(total_relations / len(pages), 2) if pages else 0
    )

    return {
        "relation_count": total_relations,
        "relation_density": relation_density,
        "generated_from_coverage": generated_from_coverage,
        "bidirectional_rate": bidirectional_rate,
        "orphan_pages": len(orphans),
        "orphan_page_list": orphans,
    }


# ── source coverage ───────────────────────────────────────────────────────────

def source_metrics(wiki_root):
    """How many raw sources generated at least one page."""
    raw_path = Path(wiki_root) / "sources" / "raw"
    raw_files = [
        f for f in raw_path.iterdir()
        if f.suffix in (".txt", ".html", ".pdf", ".md", ".json", ".csv")
        and f.name != "README.md"
    ] if raw_path.exists() else []

    manifests_path = Path(wiki_root) / "sources"
    manifests = list(manifests_path.glob("source-*.md"))

    pages_per_source = {}
    for manifest in manifests:
        fm = read_frontmatter(manifest)
        sid = fm.get("source_id", "")
        pages_created = []
        try:
            text = manifest.read_text(encoding="utf-8")
            in_pc = False
            for line in text.splitlines():
                if re.match(r'^pages_created:', line):
                    in_pc = True
                    continue
                if in_pc:
                    m = re.match(r'^\s*-\s+(.+)', line)
                    if m:
                        pages_created.append(m.group(1).strip())
                    elif re.match(r'^\w', line):
                        in_pc = False
        except Exception:
            pass
        if sid:
            pages_per_source[sid] = len(pages_created)

    sources_with_pages = sum(1 for v in pages_per_source.values() if v > 0)

    return {
        "raw_sources_total": len(raw_files),
        "manifests_created": len(manifests),
        "source_coverage_pct": round(
            sources_with_pages / len(manifests) * 100, 1
        ) if manifests else 0,
        "pages_per_source": pages_per_source,
    }


# ── cycle / agentic metrics ───────────────────────────────────────────────────

def cycle_metrics(wiki_root):
    """Extract agentic lifecycle data from absorb_log.json."""
    log_path = Path(wiki_root) / "absorb_log.json"
    try:
        records = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    ops = [r.get("operation", "") for r in records]
    requests_emitted = []
    requests_resolved = []

    for r in records:
        # evaluator requests
        for req in r.get("builder_requests", []):
            requests_emitted.append(req.get("request_id", ""))
        # reviewer requests
        for req in r.get("builder_requests_emitted", []):
            requests_emitted.append(req.get("request_id", ""))
        # resolved
        for rid in r.get("requests_resolved", []):
            requests_resolved.append(rid)

    open_requests = [r for r in requests_emitted if r not in requests_resolved]

    build_count = ops.count("build")
    eval_count  = ops.count("evaluation")
    review_count = ops.count("review")

    return {
        "operations_total": len(records),
        "operations_sequence": ops,
        "build_invocations": build_count,
        "review_invocations": review_count,
        "eval_invocations": eval_count,
        "requests_emitted_total": len(requests_emitted),
        "requests_resolved_total": len(requests_resolved),
        "open_requests_at_end": len(open_requests),
        "open_request_ids": open_requests,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def extract_metrics(wiki_root, run_id=None):
    wiki_root = str(Path(wiki_root).resolve())
    pages = collect_pages(wiki_root)

    metrics = {
        "run_id": run_id or "manual",
        "wiki_root": wiki_root,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "pages": page_metrics(pages),
        "graph": graph_metrics(pages, wiki_root),
        "sources": source_metrics(wiki_root),
        "cycle": cycle_metrics(wiki_root),
    }
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Extract benchmark metrics from a wiki run.")
    parser.add_argument("wiki_root", help="Path to wiki root directory")
    parser.add_argument("--run-id", default=None, help="Run identifier")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    args = parser.parse_args()

    metrics = extract_metrics(args.wiki_root, args.run_id)

    output_str = json.dumps(metrics, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"metrics saved -> {args.output}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
