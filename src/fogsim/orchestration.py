from __future__ import annotations

from dataclasses import dataclass

from .entities import ComputeNode, Patient, Task
from .topology import Topology


@dataclass
class NodeEstimate:
    node: ComputeNode
    tx_s: float
    exec_s: float
    queue_s: float
    mobility_s: float
    energy_j: float

    @property
    def delay_s(self) -> float:
        return self.tx_s + self.queue_s + self.exec_s + self.mobility_s

    @property
    def load_s(self) -> float:
        return self.queue_s


class ResourceManager:
    """Keeps a live view of node queues and produces placement estimates."""

    def __init__(self, topology: Topology, config: dict) -> None:
        self.topology = topology
        self.context_penalty_s = 0.03
        self.edge_processing_s = topology.edge_processing_s
        self.nodes = topology.nodes

    def queue_delay(self, node: ComputeNode) -> float:
        return node.pending_cycles / (node.speed_mcycles * max(1, node.cores))

    def estimate(self, task: Task, patient: Patient, node: ComputeNode) -> NodeEstimate:
        tx_s = self.topology.path_delay(patient.zone, node, task.size_kb)
        queue_s = self.queue_delay(node)
        exec_s = task.cycles / node.speed_mcycles
        mobility_s = 0.0
        if node.kind == "fog" and patient.last_node >= 0 and patient.last_node != node.node_id:
            mobility_s = self.context_penalty_s
        energy_j = exec_s * node.p_busy_w + self.topology.path_energy(patient.zone, node, task.size_kb)
        return NodeEstimate(node, tx_s, exec_s, queue_s, mobility_s, energy_j)

    def snapshot(self) -> list[dict]:
        return [
            {
                "node_id": node.node_id,
                "name": node.name,
                "kind": node.kind,
                "zone": node.zone,
                "pending_queue_s": round(self.queue_delay(node), 6),
                "tasks_started": node.tasks_started,
                "completed": node.completed,
            }
            for node in self.nodes
        ]


class LoadBalancer:
    """Candidate selection strategies used by the task scheduler."""

    def __init__(self) -> None:
        self._round_robin = 0

    def round_robin(self, estimates: list[NodeEstimate]) -> NodeEstimate:
        choice = estimates[self._round_robin % len(estimates)]
        self._round_robin += 1
        return choice

    @staticmethod
    def least_loaded(estimates: list[NodeEstimate]) -> NodeEstimate:
        return min(estimates, key=lambda est: (est.queue_s, est.delay_s))

    @staticmethod
    def lowest_latency(estimates: list[NodeEstimate]) -> NodeEstimate:
        return min(estimates, key=lambda est: (est.delay_s, est.queue_s))

    @staticmethod
    def weighted_score(estimates: list[NodeEstimate], weights: dict, refs: dict) -> NodeEstimate:
        def score(est: NodeEstimate) -> float:
            return (
                weights["latency"] * est.delay_s / refs["latency_s"]
                + weights["energy"] * est.energy_j / refs["energy_j"]
                + weights["load"] * est.load_s / refs["load_s"]
                + weights["mobility"] * est.mobility_s / refs["mobility_s"]
            )

        return min(estimates, key=score)


class TaskScheduler:
    """Deadline-aware scheduler and offloading decision engine."""

    def __init__(
        self,
        name: str,
        topology: Topology,
        resource_manager: ResourceManager,
        load_balancer: LoadBalancer,
        config: dict,
    ) -> None:
        self.name = name
        self.topology = topology
        self.rm = resource_manager
        self.lb = load_balancer
        self.config = config
        algorithm = config["algorithm"]
        self.safety = float(algorithm["deadline_safety_factor"])
        self.weights = dict(algorithm["weights"])
        self.refs = dict(algorithm["references"])
        self.neighbor_offload = bool(algorithm["neighbor_offload"])
        self.scheduling = "edf" if name in {"fog_edf", "proposed"} else "fcfs"
        self.prefetch = name == "proposed"

    def candidates(self, task: Task, patient: Patient) -> list[ComputeNode]:
        if self.name == "cloud_only":
            return [self.topology.cloud]
        if self.name in {"fog_rr", "fog_ll"}:
            return list(self.topology.fogs)
        local = self.topology.fogs[patient.zone % self.topology.num_fog]
        if self.neighbor_offload:
            nodes = [local] + [self.topology.fogs[j] for j in self.topology.neighbors(local.zone)]
        else:
            nodes = [local]
        if any(node.kind == "cloud" for node in nodes):
            return nodes
        return nodes + [self.topology.cloud]

    def plan(self, task: Task, patient: Patient) -> ComputeNode:
        candidates = self.candidates(task, patient)
        estimates = [self.rm.estimate(task, patient, node) for node in candidates]

        if self.name == "cloud_only":
            return self.topology.cloud
        if self.name == "fog_rr":
            return self.lb.round_robin(estimates).node
        if self.name == "fog_ll":
            return self.lb.least_loaded(estimates).node
        if self.name == "fog_edf":
            return self.lb.lowest_latency(estimates).node

        deadline = task.deadline_s * self.safety
        feasible = [est for est in estimates if est.delay_s <= deadline]
        pool = feasible if feasible else estimates
        return self.lb.weighted_score(pool, self.weights, self.refs).node


def build_scheduler(name: str, topology: Topology, config: dict) -> TaskScheduler:
    valid = {"cloud_only", "fog_rr", "fog_ll", "fog_edf", "proposed"}
    if name not in valid:
        raise ValueError(f"unknown algorithm '{name}', expected one of {sorted(valid)}")
    rm = ResourceManager(topology, config)
    return TaskScheduler(name, topology, rm, LoadBalancer(), config)
