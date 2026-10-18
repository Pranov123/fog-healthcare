from __future__ import annotations

import random
from dataclasses import dataclass

import simpy

from .entities import Patient
from .topology import Topology


@dataclass
class HandoffRecord:
    time: float
    patient_id: int
    old_zone: int
    new_zone: int
    transfer_s: float
    blocking_s: float
    prefetched: bool

    @property
    def successful(self) -> bool:
        return self.blocking_s <= 0.010


class MobilityManager:
    """Random-waypoint patient mobility with predictive context prefetch.

    A move triggers transfer of the patient context between fog nodes. Without
    prefetch the context transfer fully blocks newly generated tasks; with
    prefetch only a small residual (10%) is exposed to the task path.
    """

    def __init__(
        self,
        env: simpy.Environment,
        rng: random.Random,
        topology: Topology,
        config: dict,
        prefetch: bool,
    ) -> None:
        self.env = env
        self.rng = rng
        self.topology = topology
        self.enabled = bool(config["mobility"]["enabled"])
        self.mean_dwell_s = float(config["mobility"]["mean_dwell_s"])
        self.context_kb = float(config["workload"]["context_kb"])
        self.prefetch = prefetch
        self.records: list[HandoffRecord] = []

    def attach(self, patient: Patient) -> simpy.events.Process | None:
        if not self.enabled or self.topology.num_fog < 2:
            return None
        return self.env.process(self._move_loop(patient))

    def _move_loop(self, patient: Patient):
        while True:
            yield self.env.timeout(self.rng.expovariate(1.0 / self.mean_dwell_s))
            zones = [z for z in range(self.topology.num_fog) if z != patient.zone]
            if not zones:
                continue
            self.move(patient, self.rng.choice(zones))

    def move(self, patient: Patient, new_zone: int) -> HandoffRecord:
        old_zone = patient.zone
        link = self.topology.backbone.get((old_zone, new_zone))
        transfer = link.tx_time(self.context_kb) if link else 0.0
        blocking = transfer * (0.1 if self.prefetch else 1.0)
        patient.zone = new_zone
        patient.handoffs += 1
        patient.handoff_until = self.env.now + blocking
        record = HandoffRecord(
            time=self.env.now,
            patient_id=patient.patient_id,
            old_zone=old_zone,
            new_zone=new_zone,
            transfer_s=transfer,
            blocking_s=blocking,
            prefetched=self.prefetch,
        )
        self.records.append(record)
        return record

    def summary(self, start: float, end: float) -> dict:
        window = [r for r in self.records if start <= r.time <= end]
        if not window:
            return {
                "handoffs": 0,
                "handoff_success_pct": 100.0,
                "avg_handoff_transfer_ms": 0.0,
                "avg_handoff_blocking_ms": 0.0,
            }
        return {
            "handoffs": len(window),
            "handoff_success_pct": 100.0 * sum(r.successful for r in window) / len(window),
            "avg_handoff_transfer_ms": 1000.0 * sum(r.transfer_s for r in window) / len(window),
            "avg_handoff_blocking_ms": 1000.0 * sum(r.blocking_s for r in window) / len(window),
        }
