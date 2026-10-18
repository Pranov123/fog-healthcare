from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

ALGORITHMS = ["cloud_only", "fog_rr", "fog_ll", "fog_edf", "proposed"]
LABELS = {
    "cloud_only": "Cloud-only",
    "fog_rr": "Fog + RR",
    "fog_ll": "Fog + LL",
    "fog_edf": "Fog + latency-aware",
    "proposed": "MobiCare-Fog",
}
COLORS = {
    "cloud_only": "#6B7280",
    "fog_rr": "#F59E0B",
    "fog_ll": "#8B5CF6",
    "fog_edf": "#0EA5E9",
    "proposed": "#0E7C86",
}
CLASS_COLORS = {
    "critical": "#DC2626",
    "interactive": "#2563EB",
    "imaging": "#7C3AED",
    "batch": "#059669",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "legend.fontsize": 8,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
    }
)


def load(name: str) -> pd.DataFrame:
    path = RESULTS / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing {path}; run scripts/run_all.py first")
    return pd.read_csv(path)


def save(fig, name: str, dpi: int = 300) -> None:
    path = FIGURES / name
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def ordered(df: pd.DataFrame, column: str = "algorithm") -> pd.DataFrame:
    return df.set_index(column).loc[[a for a in ALGORITHMS if a in set(df[column])]].reset_index()


def main_latency_by_class() -> None:
    df = ordered(load("summary_all"))
    x = np.arange(len(df))
    width = 0.36

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.1))

    ax = axes[0]
    ax.bar(x - width / 2, df["critical_mean_ms"], width, label="Critical (50 ms)",
           color=CLASS_COLORS["critical"], edgecolor="white", linewidth=0.6)
    ax.bar(x + width / 2, df["interactive_mean_ms"], width, label="Interactive (300 ms)",
           color=CLASS_COLORS["interactive"], edgecolor="white", linewidth=0.6)
    ax.set_xticks(x, [LABELS[a] for a in df["algorithm"]], rotation=18, ha="right")
    ax.set_ylabel("Mean response time (ms)")
    ax.set_title("(a) Latency-sensitive classes")
    ax.legend(loc="upper left")

    ax = axes[1]
    ax.bar(x - width / 2, df["imaging_mean_ms"], width, label="Imaging (20 s)",
           color=CLASS_COLORS["imaging"], edgecolor="white", linewidth=0.6)
    ax.bar(x + width / 2, df["batch_mean_ms"], width, label="Batch (120 s)",
           color=CLASS_COLORS["batch"], edgecolor="white", linewidth=0.6)
    ax.set_xticks(x, [LABELS[a] for a in df["algorithm"]], rotation=18, ha="right")
    ax.set_ylabel("Mean response time (ms)")
    ax.set_yscale("log")
    ax.set_title("(b) Heavy classes (log scale)")
    ax.legend(loc="upper left")

    fig.suptitle("Response time by workload class at the default scenario", y=1.02, fontsize=12)
    fig.tight_layout()
    save(fig, "fig_latency_by_class.png")


def latency_cdf() -> None:
    frame = load("tasks_proposed")
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for task_class in ["critical", "interactive", "imaging", "batch"]:
        values = np.sort(frame.loc[frame["task_class"] == task_class, "latency_ms"].values)
        if len(values) == 0:
            continue
        y = np.arange(1, len(values) + 1) / len(values)
        ax.plot(values, y, color=CLASS_COLORS[task_class], linewidth=1.8,
                label=f"{task_class} (n={len(values):,})")
    ax.set_xscale("log")
    ax.set_xlabel("Response time (ms, log scale)")
    ax.set_ylabel("Cumulative fraction of tasks")
    ax.set_title("Latency distribution of MobiCare-Fog")
    ax.legend(loc="lower right")
    ax.set_ylim(0, 1.02)
    fig.tight_layout()
    save(fig, "fig_latency_cdf.png")


def energy_breakdown() -> None:
    df = ordered(load("summary_all"))
    tasks = df["tasks_completed"].replace(0, np.nan)
    fog = df["fog_energy_j"] / tasks
    cloud = df["cloud_energy_j"] / tasks
    tx = df["tx_energy_j"] / tasks
    x = np.arange(len(df))

    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    ax.bar(x, fog, color="#0E7C86", label="Fog nodes (idle + compute)",
           edgecolor="white", linewidth=0.6)
    ax.bar(x, cloud, bottom=fog, color="#2563EB", label="Cloud compute",
           edgecolor="white", linewidth=0.6)
    ax.bar(x, tx, bottom=fog + cloud, color="#F59E0B", label="Transmission",
           edgecolor="white", linewidth=0.6)
    for index, total in enumerate(fog + cloud + tx):
        ax.text(index, total + 0.025, f"{total:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, [LABELS[a] for a in df["algorithm"]], rotation=18, ha="right")
    ax.set_ylabel("Energy per completed task (J)")
    ax.set_ylim(0, float((fog + cloud + tx).max()) * 1.18)
    ax.set_title("Energy consumption and breakdown")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.tight_layout()
    save(fig, "fig_energy_breakdown.png")


def load_sweep() -> None:
    df = load("sweep_load")
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.9))

    for algorithm in ALGORITHMS:
        subset = df[df["algorithm"] == algorithm].sort_values("load_multiplier")
        if subset.empty:
            continue
        style = dict(marker="o", markersize=3.5, linewidth=1.7,
                     color=COLORS[algorithm], label=LABELS[algorithm])
        axes[0].plot(subset["load_multiplier"], subset["mean_latency_ms"], **style)
        axes[1].plot(subset["load_multiplier"], subset["tcr_pct"], **style)
        axes[2].plot(subset["load_multiplier"], subset["critical_tcr_pct"], **style)

    axes[0].set_yscale("log")
    axes[0].set_ylabel("Mean response time (ms, log)")
    axes[0].set_title("(a) Latency under load")
    axes[1].set_ylabel("Task completion rate (%)")
    axes[1].set_title("(b) Overall TCR")
    axes[1].set_ylim(0, 102)
    axes[2].set_ylabel("Critical TCR (%)")
    axes[2].set_title("(c) Critical-task TCR")
    axes[2].set_ylim(0, 102)
    for ax in axes:
        ax.set_xlabel("Workload multiplier (×)")
        ax.set_xticks(sorted(df["load_multiplier"].unique()))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle("Scalability under increasing workload", y=1.02, fontsize=12)
    fig.tight_layout()
    save(fig, "fig_load_sweep.png")


def device_scalability() -> None:
    df = load("scalability_devices")
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0))
    for algorithm in ["cloud_only", "fog_rr", "fog_edf", "proposed"]:
        subset = df[df["algorithm"] == algorithm].sort_values("patients")
        if subset.empty:
            continue
        style = dict(marker="o", markersize=3.5, linewidth=1.7,
                     color=COLORS[algorithm], label=LABELS[algorithm])
        axes[0].plot(subset["patients"], subset["mean_latency_ms"], **style)
        axes[1].plot(subset["patients"], subset["tcr_pct"], **style)
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Patients (devices)")
    axes[0].set_ylabel("Mean response time (ms, log)")
    axes[0].set_title("(a) Response time vs device count")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Patients (devices)")
    axes[1].set_ylabel("Task completion rate (%)")
    axes[1].set_ylim(0, 102)
    axes[1].set_title("(b) TCR vs device count")
    ticks = sorted(df["patients"].unique())
    for ax in axes:
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(value) for value in ticks])
        ax.minorticks_off()
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout()
    save(fig, "fig_scalability_devices.png")


def fog_scalability() -> None:
    df = load("scalability_fog")
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0))
    for algorithm in ["fog_ll", "fog_edf", "proposed"]:
        subset = df[df["algorithm"] == algorithm].sort_values("fog_nodes")
        if subset.empty:
            continue
        style = dict(marker="s", markersize=3.5, linewidth=1.7,
                     color=COLORS[algorithm], label=LABELS[algorithm])
        axes[0].plot(subset["fog_nodes"], subset["mean_latency_ms"], **style)
        axes[1].plot(subset["fog_nodes"], subset["tcr_pct"], **style)
    axes[0].set_xlabel("Fog nodes")
    axes[0].set_ylabel("Mean response time (ms)")
    axes[0].set_title("(a) Response time vs fog capacity")
    axes[1].set_xlabel("Fog nodes")
    axes[1].set_ylabel("Task completion rate (%)")
    axes[1].set_ylim(0, 102)
    axes[1].set_title("(b) TCR vs fog capacity")
    axes[0].set_xticks(sorted(df["fog_nodes"].unique()))
    axes[1].set_xticks(sorted(df["fog_nodes"].unique()))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout()
    save(fig, "fig_scalability_fog.png")


def workload_distribution() -> None:
    df = ordered(load("summary_all"))
    x = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    ax.bar(x, df["fog_share_pct"], color="#0E7C86", label="Fog",
           edgecolor="white", linewidth=0.6)
    ax.bar(x, df["cloud_share_pct"], bottom=df["fog_share_pct"], color="#2563EB",
           label="Cloud", edgecolor="white", linewidth=0.6)
    for index, cloud in enumerate(df["cloud_share_pct"]):
        ax.text(index, min(97.0, 100 - cloud / 2), f"{cloud:.1f}%", ha="center",
                va="center", color="white", fontsize=8, fontweight="bold")
    ax.set_xticks(x, [LABELS[a] for a in df["algorithm"]], rotation=18, ha="right")
    ax.set_ylabel("Share of completed tasks (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Workload distribution across fog and cloud")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2)
    fig.tight_layout()
    save(fig, "fig_workload_distribution.png")


def utilization_heatmap() -> None:
    df = load("nodes_main")
    fog = df[df["kind"] == "fog"]
    pivot = fog.pivot_table(index="algorithm", columns="name",
                            values="utilization_pct", aggfunc="first")
    pivot = pivot.reindex([a for a in ALGORITHMS if a in pivot.index])

    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    im = ax.imshow(pivot.values, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(pivot.shape[1]), pivot.columns)
    ax.set_yticks(range(pivot.shape[0]), [LABELS[a] for a in pivot.index])
    for row in range(pivot.shape[0]):
        for col in range(pivot.shape[1]):
            value = pivot.values[row, col]
            ax.text(col, row, f"{value:.1f}", ha="center", va="center",
                    fontsize=8, color="black" if value < 60 else "white")
    ax.set_title("Fog-node utilisation (%) at the default scenario")
    ax.set_xlabel("Fog node")
    fig.colorbar(im, ax=ax, label="Utilisation (%)")
    fig.tight_layout()
    save(fig, "fig_utilization_heatmap.png")


def mobility() -> None:
    df = load("mobility")
    algorithms = ["fog_edf", "proposed"]
    x = np.arange(len(algorithms))
    width = 0.34

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0))

    ax = axes[0]
    off = [df[(df["algorithm"] == a) & (~df["mobility_enabled"])]["critical_tcr_pct"].iloc[0]
           for a in algorithms]
    on = [df[(df["algorithm"] == a) & (df["mobility_enabled"])]["critical_tcr_pct"].iloc[0]
          for a in algorithms]
    ax.bar(x - width / 2, off, width, label="Mobility off", color="#94A3B8",
           edgecolor="white", linewidth=0.6)
    ax.bar(x + width / 2, on, width, label="Mobility on", color="#0E7C86",
           edgecolor="white", linewidth=0.6)
    ax.set_xticks(x, ["Fog + latency-aware", "MobiCare-Fog"])
    ax.set_ylabel("Critical-task TCR (%)")
    ax.set_ylim(0, 105)
    ax.set_title("(a) Critical completion under mobility")

    ax = axes[1]
    success = [df[(df["algorithm"] == a) & (df["mobility_enabled"])]["handoff_success_pct"].iloc[0]
               for a in algorithms]
    blocking = [df[(df["algorithm"] == a) & (df["mobility_enabled"])]["avg_handoff_blocking_ms"].iloc[0]
                for a in algorithms]
    bars = ax.bar(x, blocking, width=0.5, color=["#94A3B8", "#0E7C86"],
                  edgecolor="white", linewidth=0.6)
    for bar, pct in zip(bars, success):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                f"{pct:.0f}% success", ha="center", fontsize=8)
    ax.set_xticks(x, ["Fog + latency-aware", "MobiCare-Fog"])
    ax.set_ylabel("Mean handoff blocking time (ms)")
    ax.set_title("(b) Context-transfer interruption")
    ax.set_ylim(0, max(blocking) * 1.35)

    fig.suptitle("Mobility support with and without predictive prefetch", y=1.03, fontsize=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout()
    save(fig, "fig_mobility.png")


def radar() -> None:
    df = load("sweep_load")
    subset = df[df["load_multiplier"] == df["load_multiplier"].max()]
    subset = ordered(subset)

    def invert(values):
        span = values.max() - values.min()
        if span == 0:
            return np.ones_like(values)
        return 1.0 - (values - values.min()) / span

    scores = {
        "Critical TCR": subset["critical_tcr_pct"].values / 100.0,
        "Low latency": invert(subset["critical_mean_ms"].values),
        "Energy efficiency": invert(subset["energy_per_task_j"].values),
        "Load balance": subset["jain_index"].values,
        "Handoff success": subset["handoff_success_pct"].values / 100.0,
    }
    metrics = list(scores)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6.6, 5.8), subplot_kw={"polar": True})
    for algorithm in subset["algorithm"]:
        values = [max(0.05, scores[m][list(subset["algorithm"]).index(algorithm)])
                  for m in metrics]
        values += values[:1]
        ax.plot(angles, values, color=COLORS[algorithm], linewidth=1.8, label=LABELS[algorithm])
        ax.fill(angles, values, color=COLORS[algorithm], alpha=0.08)
    ax.set_xticks(angles[:-1], metrics)
    ax.tick_params(pad=16)
    ax.set_ylim(0, 1.05)
    ax.set_yticklabels([])
    ax.set_title(f"Normalised comparison at {int(df['load_multiplier'].max())}× load",
                 pad=22)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2)
    fig.tight_layout()
    save(fig, "fig_radar.png")


def overview() -> None:
    main = ordered(load("summary_all"))
    sweep = load("sweep_load")
    mobility_df = load("mobility")

    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.6))
    x = np.arange(len(main))

    ax = axes[0, 0]
    ax.bar(x, main["critical_mean_ms"], color=[COLORS[a] for a in main["algorithm"]],
           edgecolor="white", linewidth=0.6)
    ax.set_xticks(x, [LABELS[a] for a in main["algorithm"]], rotation=20, ha="right")
    ax.set_ylabel("ms")
    ax.set_title("(a) Critical-task response time")

    ax = axes[0, 1]
    ax.bar(x, main["energy_per_task_j"], color=[COLORS[a] for a in main["algorithm"]],
           edgecolor="white", linewidth=0.6)
    ax.set_xticks(x, [LABELS[a] for a in main["algorithm"]], rotation=20, ha="right")
    ax.set_ylabel("J per task")
    ax.set_title("(b) Energy per completed task")

    ax = axes[1, 0]
    for algorithm in ALGORITHMS:
        subset = sweep[sweep["algorithm"] == algorithm].sort_values("load_multiplier")
        if subset.empty:
            continue
        ax.plot(subset["load_multiplier"], subset["critical_tcr_pct"],
                marker="o", markersize=3.2, linewidth=1.6,
                color=COLORS[algorithm], label=LABELS[algorithm])
    ax.set_xlabel("Workload multiplier (×)")
    ax.set_ylabel("Critical TCR (%)")
    ax.set_ylim(0, 102)
    ax.set_title("(c) Critical TCR under load")
    ax.legend(fontsize=7, loc="lower left")

    ax = axes[1, 1]
    algorithms = ["fog_edf", "proposed"]
    positions = np.arange(len(algorithms))
    success = [mobility_df[(mobility_df["algorithm"] == a)
                           & (mobility_df["mobility_enabled"])]["handoff_success_pct"].iloc[0]
               for a in algorithms]
    bars = ax.bar(positions, success, width=0.5, color=["#94A3B8", "#0E7C86"],
                  edgecolor="white", linewidth=0.6)
    for bar, value in zip(bars, success):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2, f"{value:.0f}%",
                ha="center", fontsize=9)
    ax.set_xticks(positions, ["Fog + latency-aware", "MobiCare-Fog"])
    ax.set_ylim(0, 108)
    ax.set_ylabel("Handoff success (%)")
    ax.set_title("(d) Mobility handoff success")

    fig.suptitle("MobiCare-Fog evaluation overview", fontsize=13, y=1.01)
    fig.tight_layout()
    save(fig, "fig_overview.png")


def main() -> None:
    main_latency_by_class()
    latency_cdf()
    energy_breakdown()
    load_sweep()
    device_scalability()
    fog_scalability()
    workload_distribution()
    utilization_heatmap()
    mobility()
    radar()
    overview()
    print(f"\nAll figures written to {FIGURES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
