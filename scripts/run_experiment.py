from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fogsim.experiments import run_case  # noqa: E402

DISPLAY_KEYS = [
    "algorithm",
    "scheduling",
    "mobility_prefetch",
    "patients",
    "fog_nodes",
    "load_multiplier",
    "tasks_arrived",
    "tasks_completed",
    "tcr_pct",
    "critical_tcr_pct",
    "mean_latency_ms",
    "p95_latency_ms",
    "critical_mean_ms",
    "critical_p95_ms",
    "interactive_mean_ms",
    "imaging_mean_ms",
    "batch_mean_ms",
    "energy_j",
    "energy_per_task_j",
    "fog_utilization_mean",
    "jain_index",
    "fog_share_pct",
    "cloud_share_pct",
    "handoffs",
    "handoff_success_pct",
    "avg_handoff_blocking_ms",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one MobiCare-Fog scenario.")
    parser.add_argument("--algorithm", default="proposed")
    parser.add_argument("--patients", type=int, default=100)
    parser.add_argument("--load", type=float, default=1.0)
    parser.add_argument("--duration", type=int, default=600)
    parser.add_argument("--warmup", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fog-nodes", type=int, default=5)
    parser.add_argument("--no-mobility", action="store_true")
    parser.add_argument("--json", action="store_true", help="print the full summary as JSON")
    parser.add_argument("--save-tasks", action="store_true", help="write per-task CSV to results/")
    args = parser.parse_args()

    overrides = {
        "simulation": {
            "duration_s": args.duration,
            "warmup_s": args.warmup,
            "seed": args.seed,
        },
        "workload": {"num_patients": args.patients, "load_multiplier": args.load},
        "topology": {"num_fog_nodes": args.fog_nodes},
        "mobility": {"enabled": not args.no_mobility},
    }
    summary, records, nodes = run_case(args.algorithm, overrides, collect_tasks=args.save_tasks)

    if args.json:
        print(json.dumps(summary, indent=2))
        return

    print(f"\nMobiCare-Fog scenario: {args.algorithm} | patients={args.patients} "
          f"| load={args.load}x | fog_nodes={args.fog_nodes}")
    print("-" * 78)
    for key in DISPLAY_KEYS:
        value = summary.get(key)
        if isinstance(value, float):
            print(f"{key:26s} {value:12.3f}")
        else:
            print(f"{key:26s} {value}")
    print("-" * 78)
    print(f"measurement window: {summary['window_s']:.1f} s")
    print("\nNode state:")
    for node in nodes:
        print(
            f"  {node['name']:9s} util={node['utilization_pct']:6.2f}% "
            f"completed={node['completed']:6d} energy={node['energy_j']:9.1f} J"
        )

    if records:
        import pandas as pd

        outdir = ROOT / "results"
        outdir.mkdir(exist_ok=True)
        path = outdir / f"tasks_{args.algorithm}.csv"
        frame = pd.DataFrame(records)
        frame["algorithm"] = args.algorithm
        frame.to_csv(path, index=False)
        print(f"\nPer-task records written to {path}")


if __name__ == "__main__":
    main()
