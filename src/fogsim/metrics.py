from __future__ import annotations

import numpy as np

from .energy import node_energy
from .entities import ComputeNode


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def _pct(values: list[float], q: float) -> float:
    return float(np.percentile(values, q)) if values else float("nan")


class MetricsCollector:
    """Collects task records and aggregates the evaluation metrics."""

    def __init__(self, config: dict) -> None:
        simulation = config["simulation"]
        duration = float(simulation["duration_s"])
        self.warmup = float(simulation["warmup_s"])
        max_deadline = max(
            float(spec["deadline_ms"]) for spec in config["workload"]["classes"].values()
        ) / 1000.0
        self.window_start = min(self.warmup, duration)
        self.window_end = max(self.window_start + 1.0, duration - max_deadline)
        self.window_end = min(self.window_end, duration)
        self.window_s = max(1e-9, self.window_end - self.window_start)
        self.tasks = []

    def add(self, task) -> None:
        self.tasks.append(task)

    def window_tasks(self) -> list:
        return [t for t in self.tasks if self.window_start <= t.arrival <= self.window_end]

    def summarize(self, nodes: list[ComputeNode], handoff_summary: dict) -> dict:
        records = self.window_tasks()
        completed = [t for t in records if t.completed]
        met = [t for t in completed if t.met_deadline]
        arrived = len(records)
        completed_n = len(completed)

        latencies = [t.response_time for t in completed]
        fog_nodes = [n for n in nodes if n.kind == "fog"]
        cloud_nodes = [n for n in nodes if n.kind == "cloud"]

        def class_metrics(name: str) -> tuple[float, float, float]:
            values = [t.response_time for t in completed if t.task_class == name]
            met_c = [t for t in completed if t.task_class == name and t.met_deadline]
            arrived_c = [t for t in records if t.task_class == name]
            tcr_c = 100.0 * len(met_c) / len(arrived_c) if arrived_c else 0.0
            return _mean(values), _pct(values, 95), tcr_c

        crit_mean, crit_p95, crit_tcr = class_metrics("critical")
        int_mean, int_p95, _ = class_metrics("interactive")
        img_mean, img_p95, _ = class_metrics("imaging")
        bat_mean, bat_p95, _ = class_metrics("batch")

        fog_energy = sum(node_energy(n, self.window_s, n.busy_time_window) for n in fog_nodes)
        cloud_energy = sum(node_energy(n, self.window_s, n.busy_time_window) for n in cloud_nodes)
        tx_energy = sum(t.energy_j for t in records)
        total_energy = fog_energy + cloud_energy + tx_energy

        fog_utils = [
            min(1.0, n.busy_time_window / (n.cores * self.window_s))
            for n in fog_nodes
        ]
        cloud_utils = [
            min(1.0, n.busy_time_window / (n.cores * self.window_s))
            for n in cloud_nodes
        ]

        counts = [0] * len(nodes)
        for task in completed:
            if 0 <= task.dest_id < len(counts):
                counts[task.dest_id] += 1
        total_count = sum(counts)
        sumsq = sum(c * c for c in counts)
        jain = (total_count * total_count) / (len(counts) * sumsq) if sumsq else 0.0

        fog_completed = sum(1 for t in completed if t.tier == "fog")
        cloud_completed = sum(1 for t in completed if t.tier == "cloud")

        return {
            "tasks_arrived": arrived,
            "tasks_completed": completed_n,
            "tasks_met": len(met),
            "tcr_pct": 100.0 * len(met) / arrived if arrived else 0.0,
            "completion_rate_pct": 100.0 * completed_n / arrived if arrived else 0.0,
            "mean_latency_ms": 1000.0 * _mean(latencies),
            "p95_latency_ms": 1000.0 * _pct(latencies, 95),
            "p99_latency_ms": 1000.0 * _pct(latencies, 99),
            "avg_queue_delay_ms": 1000.0 * _mean([t.queue_delay for t in completed]),
            "critical_mean_ms": 1000.0 * crit_mean,
            "critical_p95_ms": 1000.0 * crit_p95,
            "critical_tcr_pct": crit_tcr,
            "interactive_mean_ms": 1000.0 * int_mean,
            "interactive_p95_ms": 1000.0 * int_p95,
            "imaging_mean_ms": 1000.0 * img_mean,
            "imaging_p95_ms": 1000.0 * img_p95,
            "batch_mean_ms": 1000.0 * bat_mean,
            "batch_p95_ms": 1000.0 * bat_p95,
            "throughput_tps": completed_n / self.window_s,
            "energy_j": total_energy,
            "energy_per_task_j": total_energy / completed_n if completed_n else 0.0,
            "fog_energy_j": fog_energy,
            "cloud_energy_j": cloud_energy,
            "tx_energy_j": tx_energy,
            "fog_utilization_mean": 100.0 * _mean(fog_utils),
            "fog_utilization_max": 100.0 * max(fog_utils) if fog_utils else 0.0,
            "cloud_utilization": 100.0 * _mean(cloud_utils),
            "jain_index": jain,
            "fog_share_pct": 100.0 * fog_completed / completed_n if completed_n else 0.0,
            "cloud_share_pct": 100.0 * cloud_completed / completed_n if completed_n else 0.0,
            "window_s": self.window_s,
            **handoff_summary,
        }

    def node_statistics(self, nodes: list[ComputeNode]) -> list[dict]:
        rows = []
        for node in nodes:
            utilization = min(1.0, node.busy_time_window / (node.cores * self.window_s))
            rows.append(
                {
                    "node_id": node.node_id,
                    "name": node.name,
                    "kind": node.kind,
                    "zone": node.zone,
                    "cores": node.cores,
                    "tasks_started": node.tasks_started,
                    "completed": node.completed,
                    "pending_queue_s": round(
                        node.pending_cycles / (node.speed_mcycles * max(1, node.cores)), 6
                    ),
                    "utilization_pct": round(100.0 * utilization, 3),
                    "energy_j": round(node_energy(node, self.window_s, node.busy_time_window), 3),
                }
            )
        return rows
