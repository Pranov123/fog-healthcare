# Fog vs Cloud Trade-offs and Architecture Justification

## 1. The trade-off in one paragraph

Local fog processing buys latency and WAN independence at the cost of idle infrastructure
energy and limited compute; cloud processing buys elastic capacity and low energy per task
at the cost of WAN latency, bandwidth contention and loss of local control. MobiCare-Fog is
therefore deliberately **hybrid**: latency-critical and interactive clinical traffic stays
on fog, while imaging and batch workloads move to the cloud when the network can absorb
them. The placement score makes this boundary explicit and deadline-aware.

## 2. Qualitative comparison

| Aspect | Local fog | Cloud | MobiCare-Fog choice |
|---|---|---|---|
| Latency | 9.8 ms critical response | 44.0 ms critical response | Fog for critical and interactive |
| Deadline protection | Short queues, EDF possible | WAN queueing can dominate | EDF on fog, deadline filter on all candidates |
| Energy per task | 1.61 J (includes idle fog power) | 1.46 J at low load | Cloud for heavy tasks; fog kept lean |
| WAN usage | Minimal | Every task traverses the WAN | Offload only imaging/batch |
| Scalability | Bounded by node cores and links | Compute elastic, WAN inelastic | Horizontal fog ring plus cloud burst |
| Mobility | Local handoff, context cache | Handoff transparent but WAN latency remains | Predictive prefetch at the fog edge |
| Privacy | Raw data stays in the hospital | Data leaves the premises | Sensitive vitals processed locally |
| Reliability | No single WAN dependency | WAN or cloud outage affects all tasks | Local critical path remains available |
| Cost | Fixed capex/opex, idle draw | Pay-as-you-go, egress charges | Avoid over-provisioning fog for imaging |
| Failure domain | Node-local | Centralised | Smaller blast radius for critical alerts |

## 3. Quantitative evidence

### 3.1 Latency

| Scenario | Local-fog policy (proposed) | Cloud-only | Difference |
|---|---|---|---|
| Critical response, 1× load | 9.8 ms | 44.0 ms | 4.5× lower on fog |
| Mean response, 1× load | 48.3 ms | 60.0 ms | 20% lower on fog |
| Critical TCR, 8× load | 93.5% | 0.0% | Cloud collapses under WAN contention |
| Critical TCR, 12× load | 85.8% | 0.0% | Fog remains usable |
| Overall TCR, 12× load | 89.0% | 1.2% | Cloud cannot drain the backlog in time |

Cloud-only is competitive only while the WAN is lightly loaded: at 1× load its TCR is
99.94%, but at 4× it falls to 83.0% and by 8× it is effectively unusable for critical care.
The WAN is the bottleneck, not cloud CPU: the cloud node is 20× faster than a fog node but
every task must cross a 200 Mbps, 40 ms link.

### 3.2 Energy

| Metric, 1× load | Proposed | Fog + RR | Cloud-only |
|---|---|---|---|
| Energy per completed task | 1.61 J | 1.69 J | 1.46 J |
| Fog energy over window | 26.0 kJ | 28.5 kJ | 21.0 kJ (idle only) |
| Cloud energy over window | 0.015 kJ | 0 | 0.044 kJ |
| Transmission energy over window | 12.3 kJ | 11.7 kJ | 13.8 kJ |

Cloud-only has the lowest energy per task at low load because it avoids five idle fog
nodes, but the gap is 9% while its critical latency is 4.5× higher. At 12× load the cloud
still uses less energy per task (0.64 J vs 0.74 J) while delivering only 1.2% TCR versus
89.0%. Energy is therefore not a reason to centralise latency-critical care; it is a reason
to avoid over-provisioning fog and to offload heavy work.

Transmission is a large, controllable share: 12.3 kJ of the proposed policy's energy over
the measurement window. Sending imaging to the cloud adds WAN energy, but avoiding 3 s of
fog CPU per 50 MB image (about 195 J) more than compensates. This is why the proposed
policy saves energy relative to round-robin while improving critical TCR.

### 3.3 Workload distribution

At 1× load MobiCare-Fog sends about 2% of tasks to the cloud; at 12× it sends about 8%.
Those cloud tasks are overwhelmingly imaging and batch studies. Critical and interactive
traffic remains on fog because the score heavily penalises added latency and because the
deadline filter rejects infeasible cloud candidates. Round-robin and least-loaded send
100% to fog and therefore pay the imaging execution energy on constrained nodes.

### 3.4 Mobility

With 16 MB of patient context, a full transfer over the fog backbone takes about 134 ms.
Without prefetch this blocks every task arriving during the handoff and no handoff meets
the 50 ms critical budget. Predictive prefetch exposes only 10% of the transfer (13.4 ms),
so all measured handoffs meet the budget and critical TCR falls by only 0.5 points
(98.82% → 98.35%) instead of 0.7 points with blocking.

## 4. Where the boundary should be drawn

For a candidate node the framework compares

```
L = edge + serialisation + propagation + link backlog + node queue + execution
E = execution power + transmission energy
```

subject to `L ≤ 0.9 × deadline`. The practical boundary that emerges is:

| Workload | Best tier | Reason |
|---|---|---|
| Critical alert (50 ms) | Local fog | WAN RTT alone consumes most of the budget |
| Interactive vitals (300 ms) | Local or neighbour fog | Fog latency is lower until its queues grow |
| Imaging (20 s, 50 MB) | Cloud | Fog execution (3 s) and local link time exceed cloud transfer plus fast execution |
| Batch (120 s, 2 MB) | Cloud | Cloud is faster and avoids occupying fog cores |
| Patient context | Fog ring + prefetch | Local handoff is faster than a cloud round trip |

If the WAN were faster or the fog nodes slower, the boundary would move toward the cloud;
if the WAN were congested, it moves toward fog. The link-backlog term is what makes the
policy react to that shift instead of assuming a static link.

## 5. Why this architecture, specifically

1. **Fog ring per hospital zone.** A ring gives each zone a local node and a neighbour for
   overflow, with 1 Gbps/3 ms links. A star or full mesh adds cost without measurable
   benefit at this scale.
2. **Five nodes, eight cores, 5,000 Mcycles/s.** Enough to keep critical execution in the
   low milliseconds while remaining a plausible small MEC server.
3. **EDF only in the proposed policy.** Critical-first ordering is the mechanism that
   protects alerts when interactive queues build; it is intentionally absent from the
   baselines so its contribution is measurable.
4. **Deadline-feasibility filter plus weighted score.** The filter prevents a low-energy
   but late choice; the score chooses among feasible candidates. This separates hard
   clinical constraints from soft optimisation.
5. **Link backlog in the estimate.** Without it, the scheduler sends work into a saturated
   WAN and then observes the delay too late.
6. **Predictive context prefetch.** Mobility is handled at the edge, where the context and
   the next zone are known, rather than at the cloud.
7. **Cloud for heavy work only.** Imaging and batch dominate bytes and CPU; centralising
   them protects fog capacity for latency-sensitive care.

## 6. When cloud-only is acceptable

Cloud-only is a reasonable choice when:

- the workload is below roughly 2× the default rate;
- imaging and batch traffic are negligible;
- the WAN has ample headroom and controlled jitter; and
- clinical deadlines are above about 100 ms.

Outside those conditions the measurements show a sharp degradation. MobiCare-Fog keeps the
cloud as an elastic back end but does not make it the critical path.

## 7. Limitations of the comparison

- The cloud is modelled as a fast node behind a fixed WAN; real cloud latency varies with
  region, peering and congestion.
- Fog idle energy dominates the energy comparison and is sensitive to the chosen power
  model; the qualitative conclusion (offload heavy work, keep critical work local) is
  robust, but absolute energy values are not.
- Mobility uses random waypoints rather than hospital traces; prefetch benefit depends on
  context size and dwell time.
- Failures, security overhead and cooling are not modelled, so reliability and cost claims
  are qualitative rather than measured.
