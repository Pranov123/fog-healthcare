from __future__ import annotations

from .entities import ComputeNode


def node_energy(node: ComputeNode, window_s: float, busy_time_s: float) -> float:
    """Energy over a window.

    ``busy_time_s`` is summed core-seconds. For fog nodes the idle draw is always
    paid; dynamic power scales with the mean core utilization. Cloud energy counts
    only the dynamic component (the cloud is assumed to exist regardless).
    """
    if window_s <= 0:
        return 0.0
    cores = max(1, node.cores)
    if node.kind == "cloud":
        return node.p_busy_w * busy_time_s / cores
    utilization = min(1.0, busy_time_s / (cores * window_s))
    return node.p_idle_w * window_s + (node.p_busy_w - node.p_idle_w) * utilization * window_s
