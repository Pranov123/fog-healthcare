from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fogsim import FogSimulation, load_config  # noqa: E402

st.set_page_config(
    page_title="MobiCare-Fog",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

ALGORITHMS = {
    "proposed": "MobiCare-Fog (proposed)",
    "fog_edf": "Fog + latency-aware (FCFS)",
    "fog_ll": "Fog + least-loaded",
    "fog_rr": "Fog + round-robin",
    "cloud_only": "Cloud-only",
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
PLOTLY_CONFIG = {"displayModeBar": False}

st.markdown(
    """
    <style>
    .block-container { padding-top: 2.0rem; padding-bottom: 2rem; }
    .hero {
        background: linear-gradient(110deg, #0E7C86 0%, #0B5E66 55%, #123B4F 100%);
        color: white; padding: 22px 28px; border-radius: 16px; margin-bottom: 18px;
    }
    .hero h1 { color: white; margin: 0 0 4px 0; font-size: 2.0rem; letter-spacing: -0.02em; }
    .hero p { color: #D7EEF1; margin: 0; font-size: 0.98rem; }
    .hero .tag {
        display: inline-block; margin-top: 10px; margin-right: 6px; padding: 3px 10px;
        border: 1px solid rgba(255,255,255,0.35); border-radius: 999px; font-size: 0.75rem;
        color: #EAF7F9;
    }
    div[data-testid="stMetric"] {
        background: #F2F7F8; border: 1px solid #DCE7E9; padding: 12px 14px;
        border-radius: 12px;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.78rem; color: #52606D; }
    div[data-testid="stMetricValue"] { font-size: 1.45rem; color: #102A33; }
    .tier-card {
        background: white; border: 1px solid #DCE7E9; border-radius: 12px;
        padding: 12px 14px; height: 100%;
    }
    .tier-card .tier-label {
        font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
        color: #0E7C86; font-weight: 700;
    }
    .tier-card .tier-title { font-weight: 700; font-size: 0.98rem; margin: 2px 0 6px 0; }
    .tier-card .tier-body { font-size: 0.8rem; color: #52606D; line-height: 1.35; }
    .small-note { color: #7B8794; font-size: 0.78rem; }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stAppDeployButton"] { display: none; }
    #MainMenu { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False, ttl=3600)
def run_simulation(
    algorithm: str,
    patients: int,
    load: float,
    fog_nodes: int,
    duration: int,
    seed: int,
    mobility: bool,
) -> tuple[dict, list[dict], list[dict]]:
    config = load_config(
        overrides={
            "algorithm": {"name": algorithm},
            "simulation": {"duration_s": duration, "warmup_s": 60, "seed": seed},
            "workload": {"num_patients": patients, "load_multiplier": load},
            "topology": {"num_fog_nodes": fog_nodes},
            "mobility": {"enabled": mobility},
        }
    )
    sim = FogSimulation(config)
    summary = sim.run()
    return summary, sim.task_records(), sim.node_statistics()


@st.cache_data(show_spinner=False, ttl=3600)
def run_comparison(
    patients: int, load: float, fog_nodes: int, duration: int, seed: int, mobility: bool
) -> pd.DataFrame:
    rows = []
    for algorithm in ALGORITHMS:
        summary, _, _ = run_simulation(
            algorithm, patients, load, fog_nodes, duration, seed, mobility
        )
        rows.append(summary)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False, ttl=3600)
def read_results(name: str) -> pd.DataFrame:
    path = ROOT / "results" / f"{name}.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=60)
def git_log(n: int = 12) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "--oneline", "--decorate", f"-{n}"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "git history unavailable"


@st.cache_data(show_spinner=False, ttl=60)
def file_commit(path: str) -> str:
    try:
        value = subprocess.check_output(
            ["git", "log", "-1", "--format=%h", "--", path], cwd=ROOT, text=True
        ).strip()
        return value or "—"
    except Exception:
        return "—"


def fmt(value, digits: int = 2, suffix: str = "") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "–"
    return f"{value:,.{digits}f}{suffix}"


def metric_card(column, label: str, value: str, help_text: str | None = None) -> None:
    column.metric(label, value, help=help_text)


# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### Scenario controls")
    algorithm = st.selectbox(
        "Policy",
        options=list(ALGORITHMS),
        format_func=lambda key: ALGORITHMS[key],
        index=0,
    )
    patients = st.slider("Patients (devices)", 20, 400, 100, 20)
    load = st.slider("Workload multiplier (×)", 1, 12, 2, 1)
    fog_nodes = st.slider("Fog nodes", 2, 10, 5, 1)
    duration = st.slider("Simulated duration (s)", 180, 900, 300, 60)
    seed = st.number_input("Random seed", min_value=1, max_value=9999, value=42, step=1)
    mobility = st.checkbox("Mobility enabled", value=True)

    st.divider()
    st.caption(
        "Measurement window excludes the 60 s warm-up and the final 120 s drain. "
        "Simulation results are comparative, not physical testbed measurements."
    )
    st.markdown(
        f"[Source code](https://github.com/Pranov123/fog-healthcare) · "
        f"[Architecture doc]({ROOT / 'docs' / 'architecture.md'})"
    )

# ----------------------------------------------------------------------------- run
with st.spinner(f"Simulating {ALGORITHMS[algorithm]}..."):
    summary, records, nodes = run_simulation(
        algorithm, patients, load, fog_nodes, duration, int(seed), mobility
    )

st.markdown(
    f"""
    <div class="hero">
      <h1>MobiCare-Fog</h1>
      <p>Integrated fog computing framework for low-latency, energy-aware smart healthcare.</p>
      <span class="tag">IoT → Edge → Fog → Cloud</span>
      <span class="tag">Deadline-aware scheduling</span>
      <span class="tag">Mobility prefetch</span>
      <span class="tag">{ALGORITHMS[algorithm]}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------- KPIs
k1, k2, k3, k4, k5, k6 = st.columns(6)
metric_card(k1, "Task completion rate", fmt(summary["tcr_pct"], 2, "%"))
metric_card(k2, "Critical p95", fmt(summary["critical_p95_ms"], 1, " ms"))
metric_card(k3, "Mean response", fmt(summary["mean_latency_ms"], 1, " ms"))
metric_card(k4, "Energy / task", fmt(summary["energy_per_task_j"], 2, " J"))
metric_card(k5, "Fog utilisation", fmt(summary["fog_utilization_mean"], 1, "%"))
if summary["handoffs"] > 0:
    metric_card(k6, "Handoff success", fmt(summary["handoff_success_pct"], 0, "%"))
else:
    metric_card(k6, "Handoff success", "n/a", "Mobility is disabled")

records_df = pd.DataFrame(records)
nodes_df = pd.DataFrame(nodes)

overview_tab, timeline_tab, scaling_tab, architecture_tab, evidence_tab = st.tabs(
    ["Overview", "Task timeline", "Scalability", "Architecture", "Build evidence"]
)

# ----------------------------------------------------------------------------- overview
with overview_tab:
    left, right = st.columns([1.35, 1])

    with left:
        st.markdown("#### Response time by workload class")
        class_frame = pd.DataFrame(
            {
                "Class": ["Critical", "Interactive", "Imaging", "Batch"],
                "Mean response (ms)": [
                    summary["critical_mean_ms"],
                    summary["interactive_mean_ms"],
                    summary["imaging_mean_ms"],
                    summary["batch_mean_ms"],
                ],
            }
        )
        fig = px.bar(
            class_frame,
            x="Mean response (ms)",
            y="Class",
            orientation="h",
            color="Class",
            color_discrete_map={
                "Critical": CLASS_COLORS["critical"],
                "Interactive": CLASS_COLORS["interactive"],
                "Imaging": CLASS_COLORS["imaging"],
                "Batch": CLASS_COLORS["batch"],
            },
            log_x=True,
            text="Mean response (ms)",
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
        fig.update_layout(
            height=320, showlegend=False, template="plotly_white",
            margin=dict(l=10, r=95, t=10, b=10),
            xaxis_title="ms (log scale)",
        )
        fig.update_xaxes(
            range=[0, np.log10(max(class_frame["Mean response (ms)"].max() * 3, 10))],
            dtick=1,
        )
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

    with right:
        st.markdown("#### Workload distribution")
        fig = go.Figure(
            go.Pie(
                labels=["Fog", "Cloud"],
                values=[summary["fog_share_pct"], summary["cloud_share_pct"]],
                hole=0.58,
                marker=dict(colors=["#0E7C86", "#2563EB"]),
                textinfo="label+percent",
                sort=False,
            )
        )
        fig.update_layout(
            height=320, template="plotly_white", showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

    lower_left, lower_right = st.columns([1, 1])
    with lower_left:
        st.markdown("#### Node utilisation")
        util = nodes_df.copy()
        util["utilisation"] = util["utilization_pct"].clip(lower=0.01)
        fig = px.bar(
            util,
            x="name",
            y="utilisation",
            color="kind",
            color_discrete_map={"fog": "#0E7C86", "cloud": "#6B7280"},
            labels={"name": "", "utilisation": "Utilisation (%)", "kind": "Tier"},
        )
        fig.update_layout(
            height=300, template="plotly_white",
            margin=dict(l=10, r=10, t=10, b=10), legend_title_text="",
        )
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

    with lower_right:
        st.markdown("#### Latest completed tasks")
        if not records_df.empty:
            event_log = records_df.sort_values("completion", ascending=False).head(10)
            display = event_log[
                ["arrival", "patient_id", "task_class", "tier", "latency_ms", "met_deadline"]
            ].copy()
            display.columns = ["Time (s)", "Patient", "Class", "Tier", "Latency (ms)", "Met"]
            display["Met"] = display["Met"].map({True: "Yes", False: "No"})
            st.dataframe(
                display.style.format({"Time (s)": "{:.1f}", "Latency (ms)": "{:.1f}"}),
                width="stretch",
                height=300,
                hide_index=True,
            )
        else:
            st.info("No completed tasks in the measurement window.")

# ----------------------------------------------------------------------------- timeline
with timeline_tab:
    st.markdown("#### Latency timeline")
    st.caption(
        "Each point is one task. Colour shows the workload class; the y-axis is logarithmic."
    )
    if not records_df.empty:
        sample = records_df
        if len(sample) > 4000:
            sample = sample.sample(4000, random_state=7)
        fig = px.scatter(
            sample,
            x="arrival",
            y="latency_ms",
            color="task_class",
            color_discrete_map=CLASS_COLORS,
            opacity=0.55,
            labels={
                "arrival": "Arrival time (s)",
                "latency_ms": "Response time (ms, log)",
                "task_class": "Class",
            },
        )
        fig.update_yaxes(type="log", dtick=1)
        fig.update_layout(
            height=380, template="plotly_white",
            margin=dict(l=10, r=10, t=10, b=10),
            legend_title_text="Class",
        )
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

    cdf_col, slow_col = st.columns([1.25, 1])
    with cdf_col:
        st.markdown("#### Latency CDF by class")
        if not records_df.empty:
            fig = go.Figure()
            for task_class, color in CLASS_COLORS.items():
                values = np.sort(
                    records_df.loc[records_df["task_class"] == task_class, "latency_ms"].values
                )
                if len(values) == 0:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=values,
                        y=np.arange(1, len(values) + 1) / len(values),
                        mode="lines",
                        name=task_class,
                        line=dict(color=color, width=2),
                    )
                )
            fig.update_xaxes(type="log", title="Response time (ms, log)", dtick=1)
            fig.update_yaxes(title="Cumulative fraction", range=[0, 1.02])
            fig.update_layout(
                height=320, template="plotly_white",
                margin=dict(l=10, r=10, t=10, b=10), legend_title_text="",
            )
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

    with slow_col:
        st.markdown("#### Slowest tasks")
        if not records_df.empty:
            slow = records_df.nlargest(8, "latency_ms")[
                ["task_class", "tier", "latency_ms", "queue_delay", "met_deadline"]
            ].copy()
            slow["queue_delay"] = slow["queue_delay"] * 1000
            slow.columns = ["Class", "Tier", "Response (ms)", "Queue (ms)", "Met"]
            slow["Met"] = slow["Met"].map({True: "Yes", False: "No"})
            st.dataframe(
                slow.style.format({"Response (ms)": "{:,.1f}", "Queue (ms)": "{:,.1f}"}),
                width="stretch",
                height=320,
                hide_index=True,
            )

# ----------------------------------------------------------------------------- scalability
with scaling_tab:
    st.markdown("#### Pre-computed scalability sweeps")
    left, right = st.columns(2)
    sweep = read_results("sweep_load").copy()
    devices = read_results("scalability_devices").copy()
    label_colors = {ALGORITHMS[key]: value for key, value in COLORS.items()}
    policy_order = [ALGORITHMS[key] for key in ALGORITHMS]
    if not sweep.empty:
        sweep["policy"] = sweep["algorithm"].map(ALGORITHMS)
    if not devices.empty:
        devices["policy"] = devices["algorithm"].map(ALGORITHMS)

    with left:
        if not sweep.empty:
            fig = px.line(
                sweep,
                x="load_multiplier",
                y="critical_tcr_pct",
                color="policy",
                markers=True,
                color_discrete_map=label_colors,
                category_orders={"policy": policy_order},
                labels={
                    "load_multiplier": "Workload multiplier (×)",
                    "critical_tcr_pct": "Critical TCR (%)",
                    "policy": "Policy",
                },
            )
            fig.update_layout(
                height=330, template="plotly_white",
                margin=dict(l=10, r=10, t=30, b=10), legend_title_text="",
                title="Critical TCR under load",
            )
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
        else:
            st.info("Run scripts/run_all.py to generate sweep results.")

    with right:
        if not devices.empty:
            fig = px.line(
                devices,
                x="patients",
                y="tcr_pct",
                color="policy",
                markers=True,
                color_discrete_map=label_colors,
                category_orders={"policy": policy_order},
                labels={
                    "patients": "Patients (devices)",
                    "tcr_pct": "Task completion rate (%)",
                    "policy": "Policy",
                },
            )
            fig.update_layout(
                height=330, template="plotly_white",
                margin=dict(l=10, r=10, t=30, b=10), legend_title_text="",
                title="TCR vs device count",
            )
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
        else:
            st.info("Run scripts/run_all.py to generate scalability results.")

    st.divider()
    st.markdown("#### Compare all five policies with the current settings")
    st.caption(
        "Runs all policies at the sidebar settings. This may take a few seconds; "
        "results are cached."
    )
    if st.button("Run five-policy comparison"):
        with st.spinner("Running five policies..."):
            comparison = run_comparison(
                patients, load, fog_nodes, min(duration, 360), int(seed), mobility
            )
        st.session_state["comparison"] = comparison

    comparison = st.session_state.get("comparison")
    if comparison is not None:
        display = comparison[
            [
                "algorithm",
                "tcr_pct",
                "critical_tcr_pct",
                "critical_mean_ms",
                "mean_latency_ms",
                "energy_per_task_j",
                "fog_utilization_mean",
                "fog_share_pct",
                "handoff_success_pct",
            ]
        ].copy()
        display["algorithm"] = display["algorithm"].map(ALGORITHMS)
        display.columns = [
            "Policy", "TCR (%)", "Critical TCR (%)", "Critical latency (ms)",
            "Mean response (ms)", "Energy/task (J)", "Fog util. (%)",
            "Fog share (%)", "Handoff success (%)",
        ]
        st.dataframe(
            display.style.format(
                {
                    "TCR (%)": "{:.2f}",
                    "Critical TCR (%)": "{:.2f}",
                    "Critical latency (ms)": "{:.1f}",
                    "Mean response (ms)": "{:.1f}",
                    "Energy/task (J)": "{:.2f}",
                    "Fog util. (%)": "{:.1f}",
                    "Fog share (%)": "{:.1f}",
                    "Handoff success (%)": "{:.0f}",
                }
            ),
            width="stretch",
            hide_index=True,
        )

        chart = comparison[["algorithm", "critical_mean_ms", "tcr_pct"]].copy()
        chart["algorithm"] = chart["algorithm"].map(ALGORITHMS)
        fig = px.bar(
            chart.melt(id_vars="algorithm", var_name="metric", value_name="value"),
            x="algorithm",
            y="value",
            color="metric",
            barmode="group",
            labels={"algorithm": "", "value": "Value", "metric": "Metric"},
            color_discrete_map={
                "critical_mean_ms": "#DC2626",
                "tcr_pct": "#0E7C86",
            },
        )
        fig.update_layout(
            height=320, template="plotly_white",
            margin=dict(l=10, r=10, t=10, b=10), legend_title_text="",
        )
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

# ----------------------------------------------------------------------------- architecture
with architecture_tab:
    st.markdown("#### Four-tier reference architecture")
    tiers = [
        ("Tier 0", "Devices & sensors", "Wearables · bedside IoT · imaging · ambulance · patient app", "#6B7280"),
        ("Tier 1", "Edge gateways", "Protocol adapter · MQTT ingest · filter/aggregate · security", "#F59E0B"),
        ("Tier 2", "Fog layer", "Scheduler · resource manager · load balancer · offloader · mobility", "#0E7C86"),
        ("Tier 3", "Cloud", "EHR · data lake · batch analytics · ML training · backup", "#2563EB"),
    ]
    columns = st.columns(4)
    for column, (label, title, body, color) in zip(columns, tiers):
        column.markdown(
            f"""
            <div class="tier-card" style="border-top:4px solid {color}">
              <div class="tier-label">{label}</div>
              <div class="tier-title">{title}</div>
              <div class="tier-body">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### Layer-by-layer flow")
    layer_table = pd.DataFrame(
        [
            ("Tier 0", "IoT devices and sensors", "Generate four classes of healthcare data continuously."),
            ("Tier 1", "Edge gateways", "Adapt protocols, ingest via MQTT, filter/aggregate, enforce security."),
            ("Tier 2", "Fog nodes", "Schedule, place, execute and migrate latency-sensitive tasks."),
            ("Tier 3", "Cloud", "Run imaging, batch analytics, EHR sync, training and backup."),
        ],
        columns=["Layer", "Component", "Role"],
    )
    st.dataframe(layer_table, width="stretch", hide_index=True)

    st.markdown("#### End-to-end task path")
    st.code(
        "sense → gateway ingest → classify task\n"
        "estimate candidates (latency, energy, queue, mobility)\n"
        "deadline filter → weighted score → select node\n"
        "transmit (serialisation + propagation + link backlog)\n"
        "EDF queue → execute → deadline check → metrics\n"
        "handoff prefetch when the patient changes zone",
        language="text",
    )
    with st.expander("Diagram specification and Mermaid draft"):
        st.markdown(
            "The full diagram contents, component table and Mermaid source are in "
            "`docs/architecture.md`. The diagram itself is produced separately for the report."
        )

# ----------------------------------------------------------------------------- evidence
with evidence_tab:
    st.markdown("#### Build history")
    st.code(git_log(), language="text")

    stages = pd.DataFrame(
        [
            ("1", "Scaffold, config and environment", "87a1c6c", "Complete"),
            ("2", "Core entities, topology and energy", "218d096", "Complete"),
            ("3", "Workload and mobility", "f9e28d9", "Complete"),
            ("4", "Scheduler, resource manager and load balancer", "ef3c647", "Complete"),
            ("5", "SimPy engine and metrics", "23cc1ef", "Complete"),
            ("6", "Architecture and workflow documentation", "1e1dbaf", "Complete"),
            ("7", "README and quickstart", "99c72bc", "Complete"),
            ("8", "Experiment suite and figures", "9194eb4", "Complete"),
            ("9", "Interactive dashboard", file_commit("dashboard/app.py"), "Complete"),
            ("10", "Literature survey and evaluation docs", "—", "In progress"),
        ],
        columns=["#", "Stage", "Commit", "Status"],
    )
    st.dataframe(stages, width="stretch", hide_index=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Result artifacts")
        artifacts = sorted(
            path.name for path in (ROOT / "results").glob("*.csv")
        )
        st.code("\n".join(artifacts) if artifacts else "no CSV results yet", language="text")
    with col_b:
        st.markdown("#### Figure artifacts")
        figures = sorted(
            path.name for path in (ROOT / "results" / "figures").glob("*.png")
        )
        st.code("\n".join(figures) if figures else "no figures yet", language="text")

    metadata_path = ROOT / "results" / "metadata.json"
    if metadata_path.exists():
        st.markdown("#### Experiment metadata")
        st.json(json.loads(metadata_path.read_text(encoding="utf-8")))

    st.caption(
        "Verification: run .\\.venv\\Scripts\\python.exe -m pytest -q. "
        "The suite covers topology, energy, mobility, all placement policies, "
        "determinism and end-to-end metrics."
    )

st.markdown(
    '<p class="small-note">MobiCare-Fog · SimPy discrete-event simulation · '
    "results are comparative, not measured on a physical testbed.</p>",
    unsafe_allow_html=True,
)
