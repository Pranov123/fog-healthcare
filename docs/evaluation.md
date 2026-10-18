# Evaluation Design and Results

All numbers in this document come from the committed CSVs in `results/` and are
reproducible from the git commit recorded in `results/metadata.json`. Each point is a
seeded, deterministic discrete-event simulation; the evaluation is comparative rather than
a physical testbed measurement.

## 1. Research questions

- **RQ1:** Does MobiCare-Fog meet critical clinical deadlines better than cloud-only,
  round-robin, least-loaded and latency-aware fog baselines?
- **RQ2:** How does response time scale with workload, device count and fog-node count?
- **RQ3:** What energy cost is paid for low latency, and where is that energy spent?
- **RQ4:** Does predictive context prefetch reduce mobility interruption without harming
  deadline performance?
- **RQ5:** How is work distributed across fog and cloud, and how evenly is fog load spread?

## 2. Simulation parameters

| Parameter | Value |
|---|---|
| Fog nodes | 5 (ring), 8 cores each, 5,000 Mcycles/s |
| Cloud | 64 cores, 100,000 Mcycles/s |
| Fog power | 10 W idle, 65 W busy |
| Cloud power | 260 W busy (dynamic only) |
| Edge link | 400 Mbps, 2 ms one-way, 1 ms gateway processing |
| Fog backbone | 1 Gbps, 3 ms one-way |
| WAN | 200 Mbps, 40 ms one-way |
| Mobility | random waypoint, mean dwell 120 s, 16 MB context |
| Simulation | 600 s default, 60 s warm-up, final 120 s drain |
| Seed | 42 |

The measurement window excludes the warm-up and drain periods so that every policy is
compared on the same steady-state arrivals.

## 3. Workload model

| Class | Mean size | CPU demand | Deadline | Deadline pressure |
|---|---|---|---|---|
| Critical | 5 KB | 30 Mcycles | 50 ms | Arrhythmia / desaturation alert |
| Interactive | 50 KB | 150 Mcycles | 300 ms | Vitals dashboard / consultation |
| Imaging | 50 MB | 15,000 Mcycles | 20 s | CT / MRI analytics |
| Batch | 2 MB | 2,000 Mcycles | 120 s | EHR sync / model retraining |

Tasks arrive as independent Poisson streams per patient and class. The default scenario has
100 patients and a 1× load multiplier; the load sweep scales all arrival rates together.

## 4. Policies

| Policy | Placement | Node scheduling |
|---|---|---|
| `cloud_only` | Always cloud | FCFS |
| `fog_rr` | Round-robin over fog nodes | FCFS |
| `fog_ll` | Least queued fog node | FCFS |
| `fog_edf` | Lowest estimated latency (local, neighbour, cloud) | FCFS |
| `proposed` | Weighted latency–energy–load–mobility score under deadline feasibility | EDF |

The proposed score is
`0.45·latency/50 ms + 0.20·energy/50 J + 0.25·queue/0.5 s + 0.10·mobility/50 ms`,
applied only to candidates whose estimated latency is at most `0.9 × deadline` whenever at
least one feasible candidate exists.

## 5. Experimental scenarios

| Scenario | Settings | Runs |
|---|---|---|
| Main comparison | 100 patients, 5 fog nodes, 1× load, 600 s | 5 |
| Load sweep | 1×–12× load, 100 patients, 400 s | 30 |
| Device scalability | 50–800 patients, 1× load, 400 s | 20 |
| Fog scalability | 2–10 fog nodes, 400 patients, 400 s | 15 |
| Mobility | on/off, 200 patients, 2× load, 60 s dwell | 4 |

Total: **74 runs** (plus per-task CSV export for the main comparison).

## 6. Metric definitions

| Metric | Definition |
|---|---|
| Response time | completion time − arrival time |
| Queue delay | execution start − arrival at the destination node |
| Energy | fog node idle + dynamic power + cloud dynamic power + link transmission energy |
| Fog utilisation | busy core-time / (cores × measurement window) |
| TCR | tasks meeting their deadline / tasks that arrived in the window |
| Critical TCR | same, restricted to critical tasks |
| Workload distribution | share of completed tasks executed on fog vs cloud |
| Load balance | Jain fairness index over per-node completed tasks |
| Handoff success | handoff blocking time ≤ 50 ms |
| Migration blocking | time a task waits because patient context is moving |

## 7. Results

### 7.1 Default scenario

| Policy | TCR (%) | Critical TCR (%) | Critical latency (ms) | Mean response (ms) | Energy/task (J) | Fog util. (%) | Fog share (%) | Handoff success (%) |
|---|---|---|---|---|---|---|---|---|
| Cloud-only | 99.94 | 99.59 | 43.99 | 60.00 | 1.46 | 0.00 | 0.0 | 0 |
| Fog + RR | 99.96 | 99.86 | 12.04 | 58.60 | 1.69 | 6.49 | 100.0 | 0 |
| Fog + LL | 99.96 | 99.86 | 11.00 | 56.82 | 1.61 | 6.49 | 100.0 | 0 |
| Fog + latency-aware | 99.96 | 99.86 | 9.81 | 48.38 | 1.61 | 4.35 | 98.1 | 0 |
| **MobiCare-Fog** | **99.97** | **99.95** | **9.79** | **48.28** | **1.61** | **4.34** | **98.0** | **100** |

At low load every policy meets most deadlines, so the separation is in latency and
mobility. MobiCare-Fog keeps critical response time at 9.8 ms versus 44.0 ms for
cloud-only. The proposed policy is statistically indistinguishable from the latency-aware
baseline here, which is expected: when queues are short, lowest-latency placement is close
to optimal. The advantage appears under stress.

### 7.2 Load sweep

Critical TCR (%):

| Load | Cloud-only | Fog + RR | Fog + LL | Fog + latency-aware | MobiCare-Fog |
|---|---|---|---|---|---|
| 1× | 99.68 | 100.00 | 100.00 | 100.00 | 100.00 |
| 2× | 95.72 | 99.59 | 99.59 | 99.59 | 99.59 |
| 4× | 74.70 | 98.70 | 97.05 | 98.73 | 98.70 |
| 6× | 22.47 | 96.73 | 81.83 | 96.79 | 96.79 |
| 8× | 0.00 | 92.38 | 48.02 | 89.65 | **93.53** |
| 12× | 0.00 | 69.93 | 14.76 | 53.65 | **85.83** |

Mean response time (ms):

| Load | Cloud-only | Fog + RR | Fog + LL | Fog + latency-aware | MobiCare-Fog |
|---|---|---|---|---|---|
| 1× | 62.0 | 61.7 | 60.0 | 50.7 | 50.6 |
| 4× | 204.9 | 62.2 | 64.7 | 55.9 | 55.8 |
| 8× | 35,075 | 87.4 | 168.3 | 90.5 | 87.8 |
| 12× | 100,568 | 154.7 | 369.8 | 178.3 | 149.7 |

Key observations:

- Cloud-only is viable below roughly 2× load but collapses beyond 4× because every task
  shares the WAN; at 8× and 12× critical TCR is zero.
- FCFS baselines lose critical deadlines as interactive work fills node queues. At 12×,
  least-loaded achieves only 14.8% critical TCR because it ignores task priority.
- EDF in MobiCare-Fog protects critical traffic: 85.8% critical TCR at 12×, 32 points above
  the latency-aware FCFS baseline (53.6%) and 16 points above round-robin (69.9%).
- Overall TCR is also highest at 12× (89.0%), because deadline-aware ordering plus
  cloud offload of heavy tasks prevents head-of-line blocking.

### 7.3 Device scalability

At 800 patients (8× the default), 1× load:

| Policy | TCR (%) | Critical TCR (%) | Mean response (ms) | Energy/task (J) | Fog util. (%) |
|---|---|---|---|---|---|
| Cloud-only | 1.92 | 0.00 | 26,215 | 0.68 | 0.00 |
| Fog + RR | 96.84 | 94.12 | 78.9 | 0.90 | 51.2 |
| Fog + latency-aware | 95.84 | 89.94 | 84.4 | 0.80 | 39.7 |
| **MobiCare-Fog** | **96.41** | **94.91** | **80.7** | **0.81** | **40.0** |

Round-robin keeps TCR close, but its critical TCR is 0.8 points lower and its energy per
task is 11% higher because it keeps imaging on fog. MobiCare-Fog matches the best TCR while
offloading heavy work and keeping fog utilisation around 40%.

### 7.4 Fog-node scalability

With 400 patients and 2–10 fog nodes, TCR rises from 93.5% to 99.8% and mean response falls
from 95.3 ms to 51.8 ms. Below three fog nodes the least-loaded policy degrades fastest
(79.0% TCR at two nodes) because its queue-blind choice overloads one node; MobiCare-Fog
stays above 93.5%. Beyond five nodes, all policies approach the network-limited floor;
adding fog capacity stops helping because link latency dominates.

### 7.5 Mobility

| Policy | Mobility | Critical TCR (%) | Mean response (ms) | Handoff success (%) | Blocking (ms) |
|---|---|---|---|---|---|
| Fog + latency-aware | off | 98.82 | 55.57 | — | 0 |
| Fog + latency-aware | on | 98.14 | 58.04 | 0 | 134.1 |
| MobiCare-Fog | off | 98.82 | 55.51 | — | 0 |
| **MobiCare-Fog** | **on** | **98.35** | **57.71** | **100** | **13.4** |

Predictive prefetch cuts the mean context-transfer interruption from 134.1 ms to 13.4 ms
(90%), moving all measured handoffs inside the 50 ms critical budget. The residual latency
cost of mobility is small (2.2 ms) because fewer tasks are exposed to the transfer.

### 7.6 Energy

At the default scenario, cloud-only uses the least energy per task (1.46 J) because it pays
no fog idle power and multiplexes compute efficiently. MobiCare-Fog uses 1.61 J, 5% less
than fog round-robin (1.69 J) and essentially the same as the latency-aware baseline.
Transmission is the dominant controllable component (about 12 kJ over the window for the
proposed policy), while fog idle power contributes roughly 26 kJ across five nodes.

Under high load the ordering changes: at 12×, cloud-only spends 0.64 J/task but delivers
89 percentage points fewer deadlines than MobiCare-Fog (0.74 J/task). The energy difference
is therefore small compared with the deadline benefit. Offloading imaging and batch work
keeps proposed fog energy at 51.7 kJ versus 61.4 kJ for round-robin while improving
critical TCR by 16 points.

### 7.7 Workload distribution and balance

The proposed policy sends about 2% of tasks to the cloud at 1× load and 8% at 12×: heavy
imaging and batch tasks move to the cloud while critical and interactive tasks stay on fog.
The Jain index is 0.862 at 1× and 0.947 at 12×, versus 0.833 for round-robin and
least-loaded (which are structurally locked to a fixed share per node). The latency-aware
baseline reaches a slightly higher Jain index at 12× (0.960) but with 32 points lower
critical TCR, showing that fairness alone is not a sufficient objective.

## 8. Findings

1. **Deadline-aware scheduling is the main source of resilience.** The gap between
   MobiCare-Fog and the latency-aware FCFS baseline grows with load, reaching 32 points of
   critical TCR at 12×.
2. **Cloud-only is not a safe fallback.** It is competitive below 2× load but its WAN
   becomes the bottleneck under imaging and batch pressure; critical TCR falls to zero.
3. **Mobility must be treated as a first-class concern.** Prefetch removes 90% of handoff
   interruption and all measured handoffs meet the critical budget.
4. **Energy and latency trade off, but not symmetrically.** Cloud-only is slightly more
   energy-efficient, yet the difference is small relative to its deadline loss at scale.
5. **Scalability is limited by the network, not only compute.** Beyond five fog nodes,
   response time flattens because link latency and backlog dominate.

## 9. Threats to validity

- **Simulation, not deployment.** Link, energy and mobility models are abstractions; a
  testbed may show different absolute values.
- **Synthetic workload.** Poisson streams and parameter values are realistic but not
  calibrated to a specific hospital. The load sweep mitigates this by testing a wide range.
- **Simplified networking.** No retransmissions, 5G variability, or congestion-control
  effects; store-and-forward links with FIFO backlog are used.
- **No failures or attacks.** Node failures, network partitions and security overhead are
  outside scope.
- **Single seed per point.** Determinism aids reproducibility but confidence intervals are
  not reported; the trends are consistent across the sweep.
- **Energy abstraction.** DVFS, cooling and embodied energy are not modelled.

## 10. Reproduce

```powershell
cd C:\Users\prano\fog-healthcare
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\run_all.py
.\.venv\Scripts\python.exe scripts\make_figures.py
.\.venv\Scripts\streamlit.exe run dashboard/app.py --server.port 8501
```

The CSVs in `results/`, the figures in `results/figures/`, and
`results/metadata.json` are the artifacts used in this document.
