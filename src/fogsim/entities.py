from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskClassSpec:
    name: str
    rate_per_patient: float
    size_kb: float
    cycles_mcycles: float
    deadline_ms: float
    rank: int
    offloadable: bool = True


def build_task_classes(config: dict) -> dict[str, TaskClassSpec]:
    specs: dict[str, TaskClassSpec] = {}
    for name, raw in config["workload"]["classes"].items():
        specs[name] = TaskClassSpec(
            name=name,
            rate_per_patient=float(raw["rate_per_patient"]),
            size_kb=float(raw["size_kb"]),
            cycles_mcycles=float(raw["cycles_mcycles"]),
            deadline_ms=float(raw["deadline_ms"]),
            rank=int(raw["rank"]),
            offloadable=bool(raw.get("offloadable", True)),
        )
    return specs


@dataclass
class Task:
    task_id: int
    task_class: str
    patient_id: int
    arrival: float
    size_kb: float
    cycles: float
    deadline_s: float
    rank: int
    zone: int
    deadline_at: float = 0.0
    dest_id: int = -1
    tier: str = ""
    handoff_wait: float = 0.0
    tx_delay: float = 0.0
    node_arrival: float = 0.0
    exec_start: float = 0.0
    queue_delay: float = 0.0
    exec_time: float = 0.0
    completion: float = 0.0
    energy_j: float = 0.0
    completed: bool = False
    met_deadline: bool = False

    def __post_init__(self) -> None:
        self.deadline_at = self.arrival + self.deadline_s

    @property
    def response_time(self) -> float:
        return self.completion - self.arrival if self.completed else float("nan")


@dataclass
class ComputeNode:
    node_id: int
    kind: str
    zone: int
    speed_mcycles: float
    cores: int
    mem_mb: float
    p_idle_w: float
    p_busy_w: float
    pending_cycles: float = 0.0
    busy_time: float = 0.0
    busy_time_window: float = 0.0
    tasks_started: int = 0
    completed: int = 0

    @property
    def name(self) -> str:
        return f"cloud-{self.node_id}" if self.kind == "cloud" else f"fog-{self.node_id}"


@dataclass
class Patient:
    patient_id: int
    zone: int
    last_node: int = -1
    handoff_until: float = 0.0
    handoffs: int = 0
    critical_session: bool = False

    @property
    def in_handoff(self) -> bool:
        return self.handoff_until > 0
