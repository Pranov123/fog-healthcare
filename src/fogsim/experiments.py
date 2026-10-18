from __future__ import annotations

import json
import platform
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import PROJECT_ROOT, deep_update, load_config
from .simulator import FogSimulation

ALGORITHMS = ["cloud_only", "fog_rr", "fog_ll", "fog_edf", "proposed"]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def run_case(
    algorithm: str,
    overrides: dict | None = None,
    collect_tasks: bool = False,
) -> tuple[dict, list[dict] | None, list[dict]]:
    merged: dict = {}
    if overrides:
        deep_update(merged, overrides)
    deep_update(merged, {"algorithm": {"name": algorithm}})
    config = load_config(overrides=merged)

    started = time.perf_counter()
    sim = FogSimulation(config)
    summary = sim.run()
    summary["wall_time_s"] = time.perf_counter() - started
    summary["scenario"] = overrides.get("scenario", "custom") if overrides else "custom"
    records = sim.task_records() if collect_tasks else None
    return summary, records, sim.node_statistics()


def _write(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False)
    print(f"  wrote {path.name} ({len(frame)} rows)", flush=True)


def _node_rows(nodes: list[dict], algorithm: str) -> list[dict]:
    rows = []
    for row in nodes:
        rows.append({**row, "algorithm": algorithm})
    return rows


def run_main(outdir: Path, quick: bool = False) -> pd.DataFrame:
    print("Running main comparison...", flush=True)
    duration = 240 if quick else 600
    warmup = 30 if quick else 60
    rows = []
    node_rows = []
    for algorithm in ALGORITHMS:
        summary, records, nodes = run_case(
            algorithm,
            {
                "scenario": "main",
                "simulation": {"duration_s": duration, "warmup_s": warmup},
            },
            collect_tasks=True,
        )
        rows.append(summary)
        node_rows.extend(_node_rows(nodes, algorithm))
        if records:
            task_frame = pd.DataFrame(records)
            task_frame["algorithm"] = algorithm
            task_frame.to_csv(outdir / f"tasks_{algorithm}.csv", index=False)
        print(
            f"  {algorithm:11s} tcr={summary['tcr_pct']:6.2f}% "
            f"latency={summary['mean_latency_ms']:8.1f} ms "
            f"energy/task={summary['energy_per_task_j']:6.2f} J",
            flush=True,
        )
    frame = pd.DataFrame(rows)
    _write(frame, outdir / "summary_all.csv")
    _write(pd.DataFrame(node_rows), outdir / "nodes_main.csv")
    return frame


def run_load_sweep(outdir: Path, quick: bool = False) -> pd.DataFrame:
    print("Running load sweep...", flush=True)
    loads = [1, 4, 8] if quick else [1, 2, 4, 6, 8, 12]
    duration = 240 if quick else 400
    warmup = 30 if quick else 40
    rows = []
    for load in loads:
        for algorithm in ALGORITHMS:
            summary, _, _ = run_case(
                algorithm,
                {
                    "scenario": "load_sweep",
                    "workload": {"load_multiplier": load},
                    "simulation": {"duration_s": duration, "warmup_s": warmup},
                },
            )
            rows.append(summary)
        print(f"  load={load}x done", flush=True)
    frame = pd.DataFrame(rows)
    _write(frame, outdir / "sweep_load.csv")
    return frame


def run_device_scalability(outdir: Path, quick: bool = False) -> pd.DataFrame:
    print("Running device scalability...", flush=True)
    patient_counts = [50, 200, 800] if quick else [50, 100, 200, 400, 800]
    algorithms = ["cloud_only", "fog_rr", "fog_edf", "proposed"]
    duration = 240 if quick else 400
    warmup = 30 if quick else 40
    rows = []
    for patients in patient_counts:
        for algorithm in algorithms:
            summary, _, _ = run_case(
                algorithm,
                {
                    "scenario": "device_scalability",
                    "workload": {"num_patients": patients, "load_multiplier": 1.0},
                    "simulation": {"duration_s": duration, "warmup_s": warmup},
                },
            )
            rows.append(summary)
        print(f"  patients={patients} done", flush=True)
    frame = pd.DataFrame(rows)
    _write(frame, outdir / "scalability_devices.csv")
    return frame


def run_fog_scalability(outdir: Path, quick: bool = False) -> pd.DataFrame:
    print("Running fog-node scalability...", flush=True)
    fog_counts = [3, 5, 8] if quick else [2, 3, 5, 8, 10]
    algorithms = ["fog_ll", "fog_edf", "proposed"]
    duration = 240 if quick else 400
    warmup = 30 if quick else 40
    rows = []
    for fog_nodes in fog_counts:
        for algorithm in algorithms:
            summary, _, _ = run_case(
                algorithm,
                {
                    "scenario": "fog_scalability",
                    "topology": {"num_fog_nodes": fog_nodes},
                    "workload": {"num_patients": 200 if quick else 400},
                    "simulation": {"duration_s": duration, "warmup_s": warmup},
                },
            )
            rows.append(summary)
        print(f"  fog_nodes={fog_nodes} done", flush=True)
    frame = pd.DataFrame(rows)
    _write(frame, outdir / "scalability_fog.csv")
    return frame


def run_mobility(outdir: Path, quick: bool = False) -> pd.DataFrame:
    print("Running mobility experiment...", flush=True)
    rows = []
    duration = 240 if quick else 400
    warmup = 30 if quick else 40
    for algorithm in ["fog_edf", "proposed"]:
        for enabled in [False, True]:
            summary, _, _ = run_case(
                algorithm,
                {
                    "scenario": "mobility",
                    "workload": {"num_patients": 120 if quick else 200, "load_multiplier": 2.0},
                    "mobility": {"enabled": enabled, "mean_dwell_s": 60},
                    "simulation": {"duration_s": duration, "warmup_s": warmup},
                },
            )
            summary["mobility_enabled"] = enabled
            rows.append(summary)
            print(
                f"  {algorithm:9s} mobility={'on' if enabled else 'off'} "
                f"handoffs={summary['handoffs']} "
                f"success={summary['handoff_success_pct']:.0f}%",
                flush=True,
            )
    frame = pd.DataFrame(rows)
    _write(frame, outdir / "mobility.csv")
    return frame


def run_all(outdir: str | Path = "results", quick: bool = False) -> dict:
    outdir = Path(outdir)
    if not outdir.is_absolute():
        outdir = PROJECT_ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)

    started = datetime.now()
    main = run_main(outdir, quick)
    load = run_load_sweep(outdir, quick)
    devices = run_device_scalability(outdir, quick)
    fog = run_fog_scalability(outdir, quick)
    mobility = run_mobility(outdir, quick)

    metadata = {
        "generated_at": started.isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "python": platform.python_version(),
        "seed": 42,
        "quick": quick,
        "runs": len(main) + len(load) + len(devices) + len(fog) + len(mobility),
        "sections": {
            "main": len(main),
            "load_sweep": len(load),
            "device_scalability": len(devices),
            "fog_scalability": len(fog),
            "mobility": len(mobility),
        },
    }
    (outdir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed {metadata['runs']} runs in {outdir}", flush=True)
    return metadata
