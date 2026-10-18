# MobiCare-Fog

**An integrated fog computing framework for low-latency, energy-aware and mobility-supported smart healthcare.**

MobiCare-Fog is a discrete-event simulation framework that models a four-tier
IoT → edge → fog → cloud healthcare pipeline. It schedules critical, interactive,
imaging and batch workloads across fog nodes and the cloud, and evaluates response
time, latency, energy, utilisation, task completion rate, workload distribution and
scalability against four baselines.

Built with Python 3.11 and [SimPy](https://simpy.readthedocs.io/), with a Streamlit
dashboard for interactive exploration and screenshot-ready figures.

---

## Highlights

- **Four-tier model** — sensors, edge gateways, a ring of fog nodes and cloud.
- **Four healthcare workload classes** with explicit deadlines:
  | Class | Example | Deadline |
  |---|---|---|
  | Critical | arrhythmia / SpO2 alert | 50 ms |
  | Interactive | vitals dashboard / consult | 300 ms |
  | Imaging | CT / MRI analytics | 20 s |
  | Batch | EHR sync / model retraining | 120 s |
- **Five placement policies** — cloud-only, fog round-robin, fog least-loaded,
  fog latency-aware (FCFS), and the proposed **MobiCare-Fog** policy.
- **Deadline-aware scheduling** — non-preemptive EDF with critical-first ordering.
- **Mobility support** — random-waypoint patients, context handoff and predictive
  prefetch.
- **Realistic network and energy models** — link serialisation, propagation,
  queue backlog, node idle/dynamic power and transmission energy.
- **Reproducible experiments** — seeded runs, YAML configuration, CSV outputs and
  300-dpi figures.

---

## Architecture

```
Tier 0  Devices          wearables · bedside IoT · imaging · ambulance · patient app
   │  BLE / Zigbee / Wi-Fi
Tier 1  Edge gateways    protocol adapter · MQTT ingest · filter/aggregate · security
   │  400 Mbps, 2 ms
Tier 2  Fog layer        scheduler · resource manager · load balancer · offloading
   │                     engine · mobility manager · context cache · analytics
   │  1 Gbps, 3 ms (ring)              200 Mbps, 40 ms (WAN)
Tier 3  Cloud            EHR · data lake · batch analytics · ML training · backup
```

A control plane overlays telemetry, policy, identity and model updates.
See [docs/architecture.md](docs/architecture.md) for the full diagram specification,
layer/component table and end-to-end task lifecycle.

### Proposed placement rule

For each candidate node the scheduler estimates:

```
latency = edge processing + serialisation + propagation
          + link backlog + node queue + execution
energy  = execution power + transmission energy
```

Candidates must satisfy `estimated_latency ≤ 0.9 × deadline`. The feasible set is
ranked by:

```
score = 0.45·(latency / 50 ms)
      + 0.20·(energy / 50 J)
      + 0.25·(queue / 0.5 s)
      + 0.10·(mobility_penalty / 50 ms)
```

Critical and interactive tasks normally stay on the local fog node; imaging and
batch workloads are offloaded to the cloud when the WAN can absorb them.

---

## Repository layout

```
fog-healthcare/
├─ configs/default.yaml        # topology, workload, mobility and algorithm parameters
├─ src/fogsim/
│  ├─ entities.py              # Task, ComputeNode, Patient, task classes
│  ├─ topology.py              # fog ring, cloud, edge/backbone/WAN links
│  ├─ workload.py              # Poisson multi-class task generation
│  ├─ mobility.py              # waypoint movement, handoff and prefetch
│  ├─ energy.py                # node and transmission energy model
│  ├─ orchestration.py         # resource manager, load balancer, scheduler, policies
│  ├─ metrics.py               # metric collection and aggregation
│  ├─ simulator.py             # SimPy discrete-event engine
│  └─ experiments.py           # experiment definitions and CSV export
├─ scripts/
│  ├─ run_experiment.py        # run one scenario from the CLI
│  ├─ run_all.py               # run the full experiment suite
│  ├─ make_figures.py          # generate evaluation figures (300 dpi)
│  └─ make_diagrams.py         # generate architecture/interaction diagrams
├─ dashboard/app.py            # Streamlit dashboard
├─ results/                    # CSV results, figures, screenshots
├─ docs/                       # architecture, evaluation, literature survey, trade-offs
└─ tests/                      # pytest unit and integration tests
```

---

## Quickstart

```powershell
git clone https://github.com/Pranov123/fog-healthcare.git
cd fog-healthcare

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m pytest -q
```

### Run one scenario

```powershell
.\.venv\Scripts\python.exe scripts\run_experiment.py --algorithm proposed --patients 200 --load 4
```

Useful flags: `--duration`, `--seed`, `--fog-nodes`, `--no-mobility`, `--json`,
`--save-tasks`.

### Run the full experiment suite

```powershell
.\.venv\Scripts\python.exe scripts\run_all.py
```

Outputs are written to `results/`:

| File | Contents |
|---|---|
| `summary_all.csv` | All five policies at the default scenario |
| `sweep_load.csv` | Load sweep (1×–12×) for every policy |
| `scalability_devices.csv` | 50–800 patients |
| `scalability_fog.csv` | 2–10 fog nodes |
| `mobility.csv` | Mobility on/off with and without prefetch |
| `nodes_main.csv` | Per-node utilisation and energy |
| `tasks_*.csv` | Per-task records for latency CDFs |

### Figures and dashboard

```powershell
.\.venv\Scripts\python.exe scripts\make_figures.py
.\.venv\Scripts\streamlit.exe run dashboard/app.py --server.port 8501
```

Open <http://localhost:8501>, choose a policy and scenario in the sidebar, and run
it. Stop the server with `Ctrl + C`.

---

## Baselines

| Policy | Placement | Node scheduling |
|---|---|---|
| `cloud_only` | Always cloud | FCFS |
| `fog_rr` | Round-robin across fog nodes | FCFS |
| `fog_ll` | Least-loaded fog node | FCFS |
| `fog_edf` | Lowest estimated latency (local / neighbour / cloud) | FCFS |
| `proposed` | Weighted latency–energy–load–mobility score under deadline constraint | EDF |

---

## Evaluation metrics

| Metric | Definition |
|---|---|
| Response time | completion time − arrival time |
| Latency | per-task network + queue + execution delay |
| Energy | node idle + dynamic power + transmission energy |
| Resource utilisation | busy core-time / (cores × measurement window) |
| Task completion rate (TCR) | tasks meeting deadline / tasks arrived |
| Workload distribution | share of completed tasks on fog vs cloud |
| Load balance | Jain fairness index over per-node completions |
| Scalability | metrics vs patient count and fog-node count |
| Mobility | handoffs, handoff success, migration blocking time |

---

## Reproducibility

- Every run is seeded from `simulation.seed` in `configs/default.yaml`.
- `results/metadata.json` records the git commit, Python version and run counts.
- Re-running the suite with the same commit and seed reproduces identical CSVs.
- Results are comparative discrete-event simulation results, not measurements from
  a physical deployment.

---

## Documentation

- [Architecture and layer flow](docs/architecture.md)
- [Literature survey](docs/literature_survey.md) *(in progress)*
- [Evaluation design](docs/evaluation.md) *(in progress)*
- [Fog vs cloud trade-offs](docs/tradeoffs.md) *(in progress)*

---

## Author

Pranov — [@Pranov123](https://github.com/Pranov123)
