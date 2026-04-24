"""
orchestrator.py — Full benchmark pipeline for Constellation Wiki.

Runs the agentic cycle (Heartbeat → Builder → Reviewer → Evaluator) against a
wiki_root, extracts metrics, and saves the full run record to benchmark/runs/.

Usage:
    python orchestrator.py <wiki_root> [options]

Options:
    --run-id       Override auto-generated run ID
    --model        Claude model to use (default: claude-sonnet-4-6)
    --max-cycles   Max Builder→Reviewer→Evaluator cycles after Heartbeat (default: 3)
    --runs-dir     Where to save run output (default: benchmark/runs/ next to this file)
    --verbose      Show agent output snippets
    --no-heartbeat Skip Heartbeat (assume sources already registered)
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.rule import Rule
from rich.text import Text
from rich.table import Table

# add pipeline dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from agent_runner import run_agent, ROLES
from metrics import extract_metrics

console = Console(highlight=False)

# ── run directory helpers ─────────────────────────────────────────────────────

def _next_run_number(runs_dir: Path) -> int:
    existing = [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run-")]
    nums = []
    for d in existing:
        parts = d.name.split("-")
        if len(parts) >= 2 and parts[1].isdigit():
            nums.append(int(parts[1]))
    return max(nums, default=-1) + 1


def make_run_dir(runs_dir: Path, run_id: str) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    n = _next_run_number(runs_dir)
    run_dir = runs_dir / f"run-{n:03d}-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


# ── stop condition ────────────────────────────────────────────────────────────

def _should_continue(eval_result: dict, cycle: int, max_cycles: int) -> bool:
    """Decide whether to run another Builder→Reviewer→Evaluator cycle."""
    if cycle >= max_cycles:
        return False
    text = eval_result.get("result", "").lower()
    # continue if evaluator emitted requests
    if "requests emitted" in text or "request" in text:
        return True
    # no-op signal
    if "no-op" in text or "no open requests" in text or "all requests resolved" in text:
        return False
    # default: stop
    return False


# ── display ───────────────────────────────────────────────────────────────────

def _print_header(wiki_root: str, run_id: str, model: str, max_cycles: int):
    console.print()
    console.rule(Text("CONSTELLATION WIKI BENCHMARK", style="bold white"))
    console.print(f"  wiki_root : [cyan]{wiki_root}[/cyan]")
    console.print(f"  run_id    : [yellow]{run_id}[/yellow]")
    console.print(f"  model     : [dim]{model}[/dim]")
    console.print(f"  max_cycles: [dim]{max_cycles}[/dim]")
    console.print()


def _print_phase(label: str):
    console.print()
    console.rule(Text(label, style="bold dim"), align="left")


def _print_metrics_summary(m: dict):
    pages = m.get("pages", {})
    graph = m.get("graph", {})
    sources = m.get("sources", {})
    cycle = m.get("cycle", {})

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="dim")
    table.add_column("value", style="bold")

    table.add_row("pages",           str(pages.get("page_count", 0)))
    table.add_row("by type",         str(pages.get("page_count_by_type", {})))
    table.add_row("relation density",str(graph.get("relation_density", 0)))
    table.add_row("gf coverage",     str(graph.get("generated_from_coverage", 0)))
    table.add_row("bidir rate",      str(graph.get("bidirectional_rate", 0)))
    table.add_row("orphans",         str(graph.get("orphan_pages", 0)))
    table.add_row("source coverage", f"{sources.get('source_coverage_pct', 0)}%")
    table.add_row("open requests",   str(cycle.get("open_requests_at_end", 0)))
    table.add_row("build invocations", str(cycle.get("build_invocations", 0)))

    console.print()
    console.rule(Text("METRICS SNAPSHOT", style="bold"))
    console.print(table)


# ── main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(
    wiki_root: str,
    run_id: str = None,
    model: str = "claude-sonnet-4-6",
    max_cycles: int = 3,
    runs_dir: Path = None,
    verbose: bool = False,
    no_heartbeat: bool = False,
) -> dict:
    """
    Run the full benchmark pipeline.

    Returns a summary dict with all agent results and final metrics.
    """
    wiki_root = str(Path(wiki_root).resolve())
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    if runs_dir is None:
        runs_dir = Path(__file__).parent.parent / "runs"

    run_dir = make_run_dir(runs_dir, run_id)
    _print_header(wiki_root, run_id, model, max_cycles)

    run_log = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "wiki_root": wiki_root,
        "model": model,
        "max_cycles": max_cycles,
        "agents": [],
        "cycles_completed": 0,
        "total_cost_usd": 0.0,
        "total_duration_s": 0.0,
    }

    t_run_start = time.time()

    # ── Phase 1: Heartbeat ────────────────────────────────────────────────────
    if not no_heartbeat:
        _print_phase("Phase 1 — Heartbeat")
        hb = run_agent("heartbeat", wiki_root, model=model, verbose=verbose)
        run_log["agents"].append(hb)
        run_log["total_cost_usd"] += hb.get("cost_usd", 0)
        run_log["total_duration_s"] += hb.get("duration_s", 0)

        if not hb["success"]:
            console.print(f"\n  [red]Heartbeat failed — aborting.[/red]")
            run_log["aborted_reason"] = "heartbeat_failed"
            _save_run(run_dir, run_id, run_log, wiki_root)
            return run_log
    else:
        console.print("  [dim]Heartbeat skipped.[/dim]")

    # ── Cycles: Build → Review → Eval ─────────────────────────────────────────
    for cycle in range(1, max_cycles + 1):
        _print_phase(f"Cycle {cycle} — Builder")
        build = run_agent("builder", wiki_root, model=model, verbose=verbose)
        run_log["agents"].append(build)
        run_log["total_cost_usd"] += build.get("cost_usd", 0)
        run_log["total_duration_s"] += build.get("duration_s", 0)

        _print_phase(f"Cycle {cycle} — Reviewer")
        review = run_agent("reviewer", wiki_root, model=model, verbose=verbose)
        run_log["agents"].append(review)
        run_log["total_cost_usd"] += review.get("cost_usd", 0)
        run_log["total_duration_s"] += review.get("duration_s", 0)

        _print_phase(f"Cycle {cycle} — Evaluator")
        evl = run_agent("evaluator", wiki_root, model=model, verbose=verbose)
        run_log["agents"].append(evl)
        run_log["total_cost_usd"] += evl.get("cost_usd", 0)
        run_log["total_duration_s"] += evl.get("duration_s", 0)

        run_log["cycles_completed"] = cycle

        if not _should_continue(evl, cycle, max_cycles):
            console.print(f"\n  [dim]No further cycles needed after cycle {cycle}.[/dim]")
            break

    # ── Final metrics ─────────────────────────────────────────────────────────
    _print_phase("Metrics")
    metrics = extract_metrics(wiki_root, run_id=run_id)
    _print_metrics_summary(metrics)

    # ── Save artifacts ────────────────────────────────────────────────────────
    run_log["finished_at"] = datetime.now(timezone.utc).isoformat()
    run_log["total_duration_s"] = round(time.time() - t_run_start, 1)
    run_log["total_cost_usd"] = round(run_log["total_cost_usd"], 6)

    _save_run(run_dir, run_id, run_log, wiki_root, metrics)

    console.print()
    console.rule(Text("RUN COMPLETE", style="bold green"))
    console.print(f"  saved -> [cyan]{run_dir}[/cyan]")
    console.print(
        f"  total: [bold]{run_log['total_duration_s']:.0f}s[/bold]  "
        f"cost: [bold]${run_log['total_cost_usd']:.4f}[/bold]  "
        f"cycles: [bold]{run_log['cycles_completed']}[/bold]"
    )
    console.print()

    return run_log


def _save_run(run_dir: Path, run_id: str, run_log: dict, wiki_root: str, metrics: dict = None):
    """Persist run_log.json and metrics.json to run_dir."""
    (run_dir / "run_log.json").write_text(
        json.dumps(run_log, indent=2), encoding="utf-8"
    )
    if metrics:
        (run_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
    console.print(f"  [dim]run_log.json + metrics.json written to {run_dir.name}[/dim]")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run the Constellation Wiki benchmark pipeline."
    )
    parser.add_argument("wiki_root", help="Path to the wiki root directory.")
    parser.add_argument("--run-id", default=None, help="Override the auto-generated run ID.")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model to use.")
    parser.add_argument("--max-cycles", type=int, default=3,
                        help="Max Builder/Reviewer/Evaluator cycles (default: 3).")
    parser.add_argument("--runs-dir", default=None,
                        help="Directory to save run artifacts (default: benchmark/runs/).")
    parser.add_argument("--verbose", action="store_true", help="Show agent output snippets.")
    parser.add_argument("--no-heartbeat", action="store_true",
                        help="Skip Heartbeat (sources already registered).")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir) if args.runs_dir else None

    run_pipeline(
        wiki_root=args.wiki_root,
        run_id=args.run_id,
        model=args.model,
        max_cycles=args.max_cycles,
        runs_dir=runs_dir,
        verbose=args.verbose,
        no_heartbeat=args.no_heartbeat,
    )


if __name__ == "__main__":
    main()
