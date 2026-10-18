# Literature Survey — Fog Computing for Smart Healthcare

## 1. Scope and method

The survey covers fog computing in healthcare, latency-sensitive scheduling, resource
management, load balancing, mobility support and energy-efficient fog computing. Papers
were located through Crossref and Semantic Scholar using the queries: *fog healthcare*,
*latency-aware task scheduling fog*, *energy-efficient fog scheduling*, *load balancing fog*,
*mobility-aware offloading fog*, and *fog simulation*. Selection criteria were:

- peer-reviewed journal or conference publication;
- a healthcare, latency-sensitive, energy, scheduling, load-balancing or mobility focus;
- a described architecture, algorithm, model or simulator; and
- publication between 2015 and 2024, with foundational work included where relevant.

Seventeen works were retained. Bibliographic metadata and DOIs were verified against
Crossref; the machine-readable records are in `docs/references_meta.json` and the BibTeX
entries in `docs/references.bib`.

## 2. Comparison matrix

| # | Study | Year | Focus | Approach / architecture | Tool / dataset | Metrics | Limitations |
|---|---|---|---|---|---|---|---|
| 1 | Rahmani et al. [1] | 2018 | Smart e-health gateway at the edge | Fog-assisted gateway with local analytics and early-warning scoring | Prototype testbed with body sensors | Latency, energy, gateway utilisation | Single-gateway scope; no multi-node scheduling or patient mobility |
| 2 | Gia et al. [2] | 2015 | ECG feature extraction near the patient | Fog node performs ECG processing before cloud upload | Prototype fog node and ECG sensor | Latency, energy, feature accuracy | Small prototype, one fog node, no load balancing or handoff |
| 3 | Tuli et al. [3] | 2020 | Deep-learning heart-disease diagnosis | Ensemble learning across IoT–fog–cloud using FogBus | FogBus; public heart-disease data | Accuracy, latency, energy, bandwidth, cost | Static placement, single disease, no mobility or deadline classes |
| 4 | Mutlag et al. [4] | 2019 | Enabling technologies for healthcare fog | Systematic review and taxonomy | Literature review | Qualitative comparison | No proposed framework or quantitative evaluation |
| 5 | Mukherjee et al. [5] | 2020 | Energy- and delay-aware health IoT | Weighted-majority game theory for fog node selection | Analytical model and simulation | Energy, delay, network lifetime | Synthetic traffic; no mobility or multi-class deadlines |
| 6 | Naha et al. [6] | 2018 | Fog architectures and requirements | Survey of trends, architectures and research directions | Literature review | Qualitative | No implementation or empirical comparison |
| 7 | Gupta et al. [7] | 2017 | Fog resource-management simulation | iFogSim toolkit for topology, placement and migration experiments | iFogSim | Latency, energy, cost, network usage | No native mobility; generic rather than healthcare-specific |
| 8 | Mahmud et al. [8] | 2022 | Mobility, clustering and microservices | iFogSim2 extension of iFogSim | iFogSim2 | Latency, energy, network usage, cost | Provides mechanisms but not a complete deadline-aware healthcare policy |
| 9 | Dastjerdi and Buyya [9] | 2016 | Fog vision and research agenda | Conceptual fog architecture | None | None | Conceptual; no evaluation |
| 10 | Sarkar and Misra [10] | 2016 | Green fog computing | Analytical latency–energy model for fog | Mathematical model | Latency, energy | Theory only; no healthcare workload, scheduling or mobility |
| 11 | Deng et al. [11] | 2020 | Edge-collaborative task allocation | Cloudlet-assisted cooperative assignment algorithms | Custom simulation | Completion time, energy, collaboration cost | Video-analysis workload; static cluster; no healthcare deadlines |
| 12 | Lim [12] | 2022 | Latency-aware scheduling with partitioning | AI-based partitioning and scheduling for small-scale fog | Simulation | Latency, deadline satisfaction, utilisation | Small-scale; partitioning overhead; no mobility or cloud tier |
| 13 | Ebneyousef and Shirmarz [13] | 2023 | Load balancing in fog | Taxonomy and survey of load-balancing algorithms | Literature review | Qualitative | No deadline-aware or healthcare-specific evaluation |
| 14 | Wang et al. [14] | 2019 | Mobility-aware offloading and migration | Optimisation of offloading and result migration under user movement | Optimisation and simulation | Latency, energy, migration cost, revenue | Generic mobile users; no clinical priority classes |
| 15 | Pakmehr et al. [15] | 2024 | Energy- and deadline-aware scheduling (ETFC) | Priority-based energy-efficient deadline scheduling | Simulation | Energy, deadline violation, makespan | Static topology; no mobility, healthcare workload or cloud coordination |
| 16 | Hosseini et al. [16] | 2022 | Priority scheduling in mobile fog | Task-prioritised energy-efficient scheduling | Simulation | Energy, response time, load balance | No healthcare validation or cloud tier |
| 17 | Shakir and Karimpour [17] | 2021 | Load balancing for healthcare fog | Survey of load-balancing approaches in smart healthcare | Literature review | Qualitative | No framework, experiment or deadline analysis |

## 3. Thematic analysis

### 3.1 Healthcare fog architectures and prototypes

The healthcare-specific literature establishes that processing near the patient reduces
latency and backhaul load. Rahmani et al. [1] place analytics and early-warning scoring in
a smart e-health gateway, while Gia et al. [2] demonstrate ECG feature extraction on a fog
node. Both report latency and energy gains but evaluate a single gateway or node, so
multi-node placement, load balancing and patient movement remain outside their scope.
HealthFog [3] moves further by distributing an ensemble deep-learning model across
IoT–fog–cloud, but uses static placement and one clinical task. Mutlag et al. [4] confirm
this pattern in their review: architectures are mature at the conceptual level, while
scheduling, mobility and energy optimisation are repeatedly listed as open issues.

### 3.2 Latency, deadlines and scheduling

Scheduling work splits into latency-aware heuristics and deadline-aware energy
optimisation. Lim [12] combines AI-based partitioning with latency-aware scheduling in
small-scale fog, and Deng et al. [11] optimise cooperative assignment across nearby edge
nodes. ETFC [15] and Hosseini et al. [16] add deadline or priority awareness to reduce
energy, but neither models clinical task classes or mobility. Across these works, latency
and energy are usually optimised separately, and few studies report deadline-met rates
per workload class.

### 3.3 Energy efficiency

Sarkar and Misra [10] formalise the latency–energy trade-off of fog, and Mukherjee et al.
[5] apply game theory to select energy-efficient fog nodes for health IoT. ETFC [15] and
Hosseini et al. [16] continue this line with priority-based scheduling. The common
limitation is abstraction: energy is optimised for synthetic workloads, while the energy
cost of transmitting large imaging payloads and the idle draw of fog infrastructure are
rarely evaluated together with deadline performance.

### 3.4 Resource management and load balancing

iFogSim [7] and iFogSim2 [8] provide the standard simulation infrastructure for placement,
migration and, in the second version, mobility and microservices. Surveys by Naha et al.
[6], Ebneyousef and Shirmarz [13] and Shakir and Karimpour [17] catalogue load-balancing
strategies, but most algorithms are evaluated on generic workloads and average latency.
Deadline-aware balancing across heterogeneous clinical traffic is not well covered.

### 3.5 Mobility support

Wang et al. [14] explicitly model user movement, radio handover and result migration, and
iFogSim2 [8] adds mobility to the simulator. However, mobility studies usually optimise
generic mobile users; they do not measure interruption of critical clinical tasks or
prefetch patient context before a handoff. The healthcare prototypes [1], [2] assume
stationary patients.

### 3.6 Simulation tools and datasets

iFogSim [7] and iFogSim2 [8] are the dominant tools, with FogBus used by HealthFog [3].
Public datasets are used mainly for diagnosis accuracy [3]; scheduling and offloading
studies typically rely on synthetic workloads. This is reasonable for comparative
evaluation, but it makes reproduction difficult when workload, topology and energy models
are under-specified.

## 4. Research gap

| Gap | Evidence in the literature | Consequence |
|---|---|---|
| **G1** Latency and energy optimised separately | [5], [10], [15], [16] | Policies trade one objective for the other without a joint score |
| **G2** No explicit clinical deadline classes | [1]–[3], [11], [15] | Critical alerts can queue behind interactive or batch work |
| **G3** Placement ignores link backlog | [7], [8], [12] | A policy may overload the WAN while fog nodes are idle |
| **G4** Mobility without handoff interruption control | [8], [14] | Context transfer can delay critical tasks after zone changes |
| **G5** Limited scalability and overload reporting | [5], [11], [15] | Behaviour beyond the tested load is unknown |
| **G6** Weak reproducibility and few baselines | [1]–[3], [12] | Results are hard to compare across studies |
| **G7** Load balancing rarely deadline-aware | [13], [17] | Fairness metrics ignore whether clinical deadlines are met |

## 5. Proposed contribution

MobiCare-Fog addresses the gaps as follows:

| Gap | MobiCare-Fog feature | Evaluation evidence |
|---|---|---|
| G1 | Weighted latency–energy–load–mobility placement score | Energy per task and latency reported together across 74 runs |
| G2 | Four clinical classes (critical 50 ms, interactive 300 ms, imaging 20 s, batch 120 s) with critical-first EDF | Critical TCR reaches 85.8% at 12× load versus 53.6% for a FCFS latency-aware baseline |
| G3 | Link backlog included in latency estimates | Proposed avoids sending critical flows into a saturated WAN; total TCR 89.0% at 12× load |
| G4 | Random-waypoint mobility with predictive context prefetch | Handoff success 100% versus 0% and blocking time 13.4 ms versus 134.1 ms |
| G5 | Device scalability to 800 patients, 2–10 fog nodes, 1–12× load | 96.4% TCR at 800 patients versus 1.9% for cloud-only |
| G6 | Open-source, seeded simulator with five policies and 19 tests | Reproducible CSVs, figures and metadata |
| G7 | Load balancing compared against RR, least-loaded and latency-aware policies | Jain index and per-class TCR reported |

## 6. Positioning

MobiCare-Fog is not a new sensor gateway like [1], [2], nor a new simulator like [7], [8].
It is an orchestration framework evaluated inside a reproducible simulator: it combines
deadline-aware scheduling, joint latency–energy–load–mobility placement, link-backlog
awareness and predictive handoff in one policy, and compares that policy with four
baselines on the same multi-class healthcare workload. This directly targets the
integration gap visible across the surveyed work.

## 7. References

[1] A. M. Rahmani, T. N. Gia, B. Negash, A. Anzanpour, I. Azimi, M. Jiang, and P. Liljeberg, "Exploiting smart e-Health gateways at the edge of healthcare Internet-of-Things: A fog computing approach," *Future Generation Computer Systems*, vol. 78, pp. 641–658, 2018, doi: [10.1016/j.future.2017.02.014](https://doi.org/10.1016/j.future.2017.02.014).

[2] T. N. Gia, M. Jiang, A.-M. Rahmani, T. Westerlund, P. Liljeberg, and H. Tenhunen, "Fog computing in healthcare Internet of Things: A case study on ECG feature extraction," in *Proc. IEEE CIT/IUCC/DASC/PICOM*, 2015, pp. 356–363, doi: [10.1109/CIT/IUCC/DASC/PICOM.2015.51](https://doi.org/10.1109/CIT/IUCC/DASC/PICOM.2015.51).

[3] S. Tuli, N. Basumatary, S. S. Gill, M. Kahani, R. C. Arya, G. S. Wander, and R. Buyya, "HealthFog: An ensemble deep learning based smart healthcare system for automatic diagnosis of heart diseases in integrated IoT and fog computing environments," *Future Generation Computer Systems*, vol. 104, pp. 187–200, 2020, doi: [10.1016/j.future.2019.10.043](https://doi.org/10.1016/j.future.2019.10.043).

[4] A. A. Mutlag, M. K. Abd Ghani, N. Arunkumar, M. A. Mohammed, and O. Mohd, "Enabling technologies for fog computing in healthcare IoT systems," *Future Generation Computer Systems*, vol. 90, pp. 62–78, 2019, doi: [10.1016/j.future.2018.07.049](https://doi.org/10.1016/j.future.2018.07.049).

[5] A. Mukherjee, D. De, and S. K. Ghosh, "FogIoHT: A weighted majority game theory based energy-efficient delay-sensitive fog network for internet of health things," *Internet of Things*, vol. 11, art. 100181, 2020, doi: [10.1016/j.iot.2020.100181](https://doi.org/10.1016/j.iot.2020.100181).

[6] R. K. Naha, S. Garg, D. Georgakopoulos, P. P. Jayaraman, L. Gao, Y. Xiang, and R. Ranjan, "Fog computing: Survey of trends, architectures, requirements, and research directions," *IEEE Access*, vol. 6, pp. 47980–48009, 2018, doi: [10.1109/ACCESS.2018.2866491](https://doi.org/10.1109/ACCESS.2018.2866491).

[7] H. Gupta, A. V. Dastjerdi, S. K. Ghosh, and R. Buyya, "iFogSim: A toolkit for modeling and simulation of resource management techniques in the Internet of Things, edge and fog computing environments," *Software: Practice and Experience*, vol. 47, no. 9, pp. 1275–1296, 2017, doi: [10.1002/spe.2509](https://doi.org/10.1002/spe.2509).

[8] R. Mahmud, S. Pallewatta, M. Goudarzi, and R. Buyya, "iFogSim2: An extended iFogSim simulator for mobility, clustering, and microservice management in edge and fog computing environments," *Journal of Systems and Software*, vol. 190, art. 111351, 2022, doi: [10.1016/j.jss.2022.111351](https://doi.org/10.1016/j.jss.2022.111351).

[9] A. V. Dastjerdi and R. Buyya, "Fog computing: Helping the Internet of Things realize its potential," *Computer*, vol. 49, no. 8, pp. 112–116, 2016, doi: [10.1109/MC.2016.245](https://doi.org/10.1109/MC.2016.245).

[10] S. Sarkar and S. Misra, "Theoretical modelling of fog computing: A green computing paradigm to support IoT applications," *IET Networks*, vol. 5, no. 2, pp. 23–29, 2016, doi: [10.1049/iet-net.2015.0034](https://doi.org/10.1049/iet-net.2015.0034).

[11] X. Deng, J. Li, E. Liu, and H. Zhang, "Task allocation algorithm and optimization model on edge collaboration," *Journal of Systems Architecture*, vol. 110, art. 101778, 2020, doi: [10.1016/j.sysarc.2020.101778](https://doi.org/10.1016/j.sysarc.2020.101778).

[12] J. Lim, "Latency-aware task scheduling for IoT applications based on artificial intelligence with partitioning in small-scale fog computing environments," *Sensors*, vol. 22, no. 19, art. 7326, 2022, doi: [10.3390/s22197326](https://doi.org/10.3390/s22197326).

[13] S. Ebneyousef and A. Shirmarz, "A taxonomy of load balancing algorithms and approaches in fog computing: A survey," *Cluster Computing*, vol. 26, pp. 3187–3208, 2023, doi: [10.1007/s10586-023-03982-3](https://doi.org/10.1007/s10586-023-03982-3).

[14] D. Wang, Z. Liu, X. Wang, and Y. Lan, "Mobility-aware task offloading and migration schemes in fog computing networks," *IEEE Access*, vol. 7, pp. 43356–43368, 2019, doi: [10.1109/ACCESS.2019.2908263](https://doi.org/10.1109/ACCESS.2019.2908263).

[15] A. Pakmehr, M. Gholipour, and E. Zeinali, "ETFC: Energy-efficient and deadline-aware task scheduling in fog computing," *Sustainable Computing: Informatics and Systems*, vol. 42, art. 100988, 2024, doi: [10.1016/j.suscom.2024.100988](https://doi.org/10.1016/j.suscom.2024.100988).

[16] E. Hosseini, M. Nickray, and S. Ghanbari, "Energy-efficient scheduling based on task prioritization in mobile fog computing," *Computing*, vol. 105, pp. 361–383, 2022, doi: [10.1007/s00607-022-01108-y](https://doi.org/10.1007/s00607-022-01108-y).

[17] H. M. Shakir and J. Karimpour, "Survey on load balancing in fog computing in smart healthcare system," in *Proc. Int. Conf. Advanced Computer Applications (ACA)*, 2021, doi: [10.1109/ACA52198.2021.9626783](https://doi.org/10.1109/ACA52198.2021.9626783).
