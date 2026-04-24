"""
report.py — Cross-run comparison report for Constellation Wiki benchmark.

Reads all run-NNN-* directories from benchmark/runs/, loads their metrics.json,
and prints a comparative table plus delta vs the baseline (run-000-*).

Usage:
    python report.py [--runs-dir <path>] [--baseline <run-id-prefix>]
    python report.py                          # auto-discovers runs
    python report.py --baseline run-000       # compare vs specific baseline
"""

import argparse
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console(highlight=False)

# Metrics to display in the table, with display name and format
METRIC_SPECS = [
    # (key_path, display_name, format_str, higher_is_better)
    ("pages.page_count",                   "pages",         "d",    True),
    ("pages.page_count_by_type.entity",    "entities",      "d",    True),
    ("pages.page_count_by_type.concept",   "concepts",      "d",    True),
    ("pages.page_count_by_type.playbook",  "playbooks",     "d",    True),
    ("pages.page_count_by_type.synthesis", "synthesis",     "d",    True),
    ("pages.mean_page_length",             "mean_lines",    ".1f",  True),
    ("graph.relation_density",             "rel_density",   ".2f",  True),
    ("graph.generated_from_coverage",      "gf_coverage",   ".3f",  True),
    ("graph.bidirectional_rate",           "bidir_rate",    ".3f",  True),
    ("graph.orphan_pages",                 "orphans",       "d",    False),
    ("sources.source_coverage_pct",        "src_coverage%", ".1f",  True),
    ("sources.manifests_created",          "manifests",     "d",    True),
    ("cycle.build_invocations",            "builds",        "d",    None),
    ("cycle.requests_emitted_total",       "req_emitted",   "d",    None),
    ("cycle.open_requests_at_end",         "open_reqs",     "d",    False),
]


def _get_nested(d: dict, key_path: str):
    """Traverse a.b.c key into nested dict."""
    parts = key_path.split(".")
    val = d
    for p in parts:
        if not isinstance(val, dict):
            return None
        val = val.get(p)
    return val


def load_runs(runs_dir: Path) -> list[dict]:
    """Load all run directories sorted by run number."""
    runs = []
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("run-"):
            continue
        metrics_path = d / "metrics.json"
        run_log_path = d / "run_log.json"
        if not metrics_path.exists():
            continue
        m = json.loads(metrics_path.read_text(encoding="utf-8"))
        log = {}
        if run_log_path.exists():
            log = json.loads(run_log_path.read_text(encoding="utf-8"))
        runs.append({
            "dir": d.name,
            "run_id": m.get("run_id", d.name),
            "metrics": m,
            "log": log,
        })
    return runs


def _fmt(val, fmt: str) -> str:
    if val is None:
        return "[dim]-[/dim]"
    try:
        return format(val, fmt)
    except Exception:
        return str(val)


def _delta_str(val, baseline, higher_is_better) -> str:
    if val is None or baseline is None or higher_is_better is None:
        return ""
    try:
        delta = val - baseline
        if delta == 0:
            return "[dim]=[/dim]"
        sign = "+" if delta > 0 else ""
        color = "green" if (delta > 0) == higher_is_better else "red"
        return f"[{color}]{sign}{delta:g}[/{color}]"
    except Exception:
        return ""


def print_comparison_table(runs: list[dict], baseline_prefix: str = None):
    if not runs:
        console.print("[red]No runs found.[/red]")
        return

    # identify baseline
    baseline = None
    if baseline_prefix:
        for r in runs:
            if r["dir"].startswith(baseline_prefix):
                baseline = r
                break
    if baseline is None:
        baseline = runs[0]  # first run is baseline

    console.print()
    console.rule(Text("BENCHMARK COMPARISON", style="bold white"))
    console.print(f"  baseline: [cyan]{baseline['dir']}[/cyan]")
    console.print(f"  runs    : {len(runs)}")
    console.print()

    # build table
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("metric", style="dim", min_width=14)

    for r in runs:
        label = r["dir"]
        style = "cyan" if r is baseline else "white"
        table.add_column(label, style=style, justify="right", min_width=10)

    for key_path, display, fmt, higher in METRIC_SPECS:
        row = [display]
        base_val = _get_nested(baseline["metrics"], key_path)

        for r in runs:
            val = _get_nested(r["metrics"], key_path)
            val_str = _fmt(val, fmt)
            if r is not baseline:
                d_str = _delta_str(val, base_val, higher)
                if d_str:
                    val_str = f"{val_str} {d_str}"
            row.append(val_str)

        table.add_row(*row)

    console.print(table)

    # cost / duration summary
    console.print()
    console.rule(Text("RUN COSTS", style="bold dim"), align="left")
    cost_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    cost_table.add_column("run", style="dim")
    cost_table.add_column("duration_s", justify="right")
    cost_table.add_column("cost_usd", justify="right")
    cost_table.add_column("cycles", justify="right")
    cost_table.add_column("builds", justify="right")

    for r in runs:
        lg = r["log"]
        cost_table.add_row(
            r["dir"],
            str(lg.get("total_duration_s", "-")),
            f"${lg.get('total_cost_usd', 0):.4f}" if lg else "-",
            str(lg.get("cycles_completed", "-")),
            str(_get_nested(r["metrics"], "cycle.build_invocations") or "-"),
        )

    console.print(cost_table)
    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="Print cross-run comparison table for the Constellation Wiki benchmark."
    )
    parser.add_argument(
        "--runs-dir", default=None,
        help="Path to benchmark/runs/ directory. Defaults to ../runs relative to this file."
    )
    parser.add_argument(
        "--baseline", default=None,
        help="Prefix of the baseline run dir (e.g. 'run-000'). Defaults to first run."
    )
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir) if args.runs_dir else Path(__file__).parent.parent / "runs"

    if not runs_dir.exists():
        console.print(f"[red]runs_dir not found: {runs_dir}[/red]")
        return

    runs = load_runs(runs_dir)
    print_comparison_table(runs, args.baseline)


if __name__ == "__main__":
    main()
