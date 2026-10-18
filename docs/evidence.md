# Screenshot and Evidence Checklist

Every stage leaves a reproducible artifact. Run each command from the project root and
capture the terminal, editor or browser region with `Win + Shift + S`; save the PNG in
`results/screenshots/` using the suggested name.

## One-time setup

```powershell
cd C:\Users\prano\fog-healthcare
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: `19 passed`.

## Section-by-section evidence

| # | Stage | Evidence to capture | Command / location | Save as |
|---|---|---|---|---|
| 1 | Requirements and scenario | Four workload classes, deadlines and topology parameters | Open `configs\default.yaml` in VS Code (lines 1–75) | `01-requirements.png` |
| 2 | Environment | Python and package versions, remote | `.\.venv\Scripts\python.exe --version; .\.venv\Scripts\pip list; git remote -v` | `02-environment.png` |
| 3 | Core model | Passing core tests | `.\.venv\Scripts\python.exe -m pytest tests\test_core.py -q` | `03-core-model.png` |
| 4 | Workload and mobility | Passing workload/mobility tests | `.\.venv\Scripts\python.exe -m pytest tests\test_workload_mobility.py -q` | `04-workload-mobility.png` |
| 5 | Orchestration | Passing policy tests | `.\.venv\Scripts\python.exe -m pytest tests\test_orchestration.py -q` | `05-orchestration.png` |
| 6 | Simulator and metrics | One scenario with metric table | `.\.venv\Scripts\python.exe scripts\run_experiment.py --algorithm proposed --patients 200 --load 4` | `06-simulator.png` |
| 7 | Calibration and debugging | Commit history plus stress behaviour | `git log --oneline -10`; `.\.venv\Scripts\python.exe scripts\run_experiment.py --algorithm proposed --patients 100 --load 12` | `07-calibration.png` |
| 8 | Validation | Full suite passing | `.\.venv\Scripts\python.exe -m pytest -q` | `08-validation.png` |
| 9 | Experiment results | Summary CSV and figures | `.\.venv\Scripts\python.exe scripts\make_figures.py`; open `results\summary_all.csv` and `results\figures\` | `09-results.png` |
| 10 | Dashboard | Running dashboard, all tabs | see below | `10-dashboard-*.png` |
| 11 | Documentation | Literature table and references | Open `docs\literature_survey.md` and `docs\references.bib` | `11-docs.png` |

## Dashboard screenshots

Start the dashboard:

```powershell
cd C:\Users\prano\fog-healthcare
.\.venv\Scripts\streamlit.exe run dashboard/app.py --server.port 8501
```

Open <http://localhost:8501>. The default scenario is MobiCare-Fog, 100 patients, 2× load,
5 fog nodes, 300 s, seed 42 (the page runs automatically).

| Screenshot | How to produce it | Save as |
|---|---|---|
| Default overview | Load the page; capture hero, six KPI cards, class latency, workload donut, node utilisation and task table | `10a-dashboard-overview.png` |
| Task timeline | Click **Task timeline**; capture scatter and CDF | `10b-dashboard-timeline.png` |
| Load stress | Set **Policy** to *Cloud-only* and **Workload multiplier** to 8; capture KPIs; then switch back to *MobiCare-Fog* and capture the same view | `10c-cloud-load8.png`, `10d-proposed-load8.png` |
| Policy comparison | Click **Scalability**, then **Run five-policy comparison**; capture the table and chart | `10e-comparison.png` |
| Scalability sweeps | On **Scalability**, capture the two pre-computed line charts | `10f-scalability.png` |
| Architecture | Click **Architecture**; capture the four tier cards, layer table and task path | `10g-architecture.png` |
| Build evidence | Click **Build evidence**; capture the commit history and stage table | `10h-build-evidence.png` |

Stop the server with `Ctrl + C`.

## Result figures to insert in the report

`results/figures/` contains 300-dpi PNGs:

- `fig_latency_by_class.png`
- `fig_latency_cdf.png`
- `fig_energy_breakdown.png`
- `fig_load_sweep.png`
- `fig_scalability_devices.png`
- `fig_scalability_fog.png`
- `fig_workload_distribution.png`
- `fig_utilization_heatmap.png`
- `fig_mobility.png`
- `fig_radar.png`
- `fig_overview.png`

## If a screenshot fails

- Use a maximised window and `Ctrl + Scroll` to increase terminal font size.
- Crop tightly: command plus the key few lines is enough.
- For the dashboard, wait until the KPI cards show numbers before capturing.
- If Streamlit is already using port 8501, either stop the old process or choose
  `--server.port 8502`.
