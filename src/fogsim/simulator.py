from __future__ import annotations

import itertools
import random
from dataclasses import asdict

import simpy

from .entities import Task, build_task_classes
from .metrics import MetricsCollector
from .mobility import MobilityManager
from .orchestration import build_scheduler
from .topology import Topology
from .workload import spawn_patients, task_stream


class FogSimulation:
    """Discrete-event simulation of the integrated fog healthcare framework."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.env = simpy.Environment()
        self.rng = random.Random(int(config["simulation"]["seed"]))
        self.topology = Topology(self.env, config)
        self.scheduler = build_scheduler(config["algorithm"]["name"], self.topology, config)
        self.mobility = MobilityManager(
            self.env,
            self.rng,
            self.topology,
            config,
            prefetch=bool(config["mobility"].get("handoff_prefetch", True))
            and self.scheduler.prefetch,
        )
        self.classes = build_task_classes(config)
        self.patients = spawn_patients(
            int(config["workload"]["num_patients"]),
            self.topology.num_fog,
            self.rng,
        )
        self.metrics = MetricsCollector(config)
        self.duration_s = float(config["simulation"]["duration_s"])
        self._task_ids = itertools.count(1)
        self.tasks: list[Task] = []
        self.stores = {
            node.node_id: simpy.PriorityStore(self.env) for node in self.topology.nodes
        }
        self._started = False

    def make_task(self, patient, spec) -> Task:
        return Task(
            task_id=next(self._task_ids),
            task_class=spec.name,
            patient_id=patient.patient_id,
            arrival=self.env.now,
            size_kb=spec.size_kb,
            cycles=spec.cycles_mcycles,
            deadline_s=spec.deadline_ms / 1000.0,
            rank=spec.rank,
            zone=patient.zone,
        )

    def _emit(self, patient, spec) -> None:
        task = self.make_task(patient, spec)
        self.tasks.append(task)
        self.env.process(self._handle_task(task, patient))

    def _handle_task(self, task: Task, patient):
        wait = max(0.0, patient.handoff_until - self.env.now)
        if wait > 0:
            yield self.env.timeout(wait)
        task.handoff_wait = wait
        task.zone = patient.zone

        node = self.scheduler.plan(task, patient)
        task.dest_id = node.node_id
        task.tier = node.kind

        tx_start = self.env.now
        if self.topology.edge_processing_s > 0:
            yield self.env.timeout(self.topology.edge_processing_s)
        for link in self.topology.path(patient.zone, node):
            serialization = link.serialization_time(task.size_kb)
            link.pending_s += serialization
            with link.resource.request() as request:
                yield request
                yield self.env.timeout(serialization)
            link.pending_s = max(0.0, link.pending_s - serialization)
            yield self.env.timeout(link.latency_ms / 1000.0)
            link.transmissions += 1
            link.bytes_sent += task.size_kb * 1024.0

        task.tx_delay = self.env.now - tx_start
        task.node_arrival = self.env.now
        task.energy_j += self.topology.path_energy(patient.zone, node, task.size_kb)

        node.pending_cycles += task.cycles
        if self.scheduler.scheduling == "edf":
            key = task.deadline_at + task.rank * 1e-9
        else:
            key = float(task.task_id)
        yield self.stores[node.node_id].put((key, task.task_id, task))

    def _worker(self, node):
        store = self.stores[node.node_id]
        while True:
            _, _, task = yield store.get()
            node.tasks_started += 1
            task.exec_start = self.env.now
            task.queue_delay = task.exec_start - task.node_arrival

            exec_time = task.cycles / node.speed_mcycles
            yield self.env.timeout(exec_time)

            node.completed += 1
            node.pending_cycles = max(0.0, node.pending_cycles - task.cycles)
            overlap_lo = max(task.exec_start, self.metrics.window_start)
            overlap_hi = min(self.env.now, self.metrics.window_end)
            if overlap_hi > overlap_lo:
                node.busy_time_window += overlap_hi - overlap_lo

            task.exec_time = exec_time
            task.completion = self.env.now
            task.completed = True
            task.met_deadline = self.env.now <= task.deadline_at
            self.patients[task.patient_id].last_node = node.node_id
            self.metrics.add(task)

    def run(self) -> dict:
        if self._started:
            raise RuntimeError("simulation instances can only run once")
        self._started = True

        for node in self.topology.nodes:
            for _ in range(node.cores):
                self.env.process(self._worker(node))

        multiplier = float(self.config["workload"].get("load_multiplier", 1.0))
        for patient in self.patients:
            for spec in self.classes.values():
                task_stream(
                    self.env,
                    self.rng,
                    patient,
                    spec,
                    spec.rate_per_patient * multiplier,
                    self._emit,
                )
            self.mobility.attach(patient)

        self.env.run(until=self.duration_s)
        return self.summary()

    def summary(self) -> dict:
        handoffs = self.mobility.summary(self.metrics.window_start, self.metrics.window_end)
        summary = self.metrics.summarize(self.topology.nodes, handoffs)
        summary.update(
            {
                "algorithm": self.scheduler.name,
                "patients": len(self.patients),
                "fog_nodes": self.topology.num_fog,
                "seed": int(self.config["simulation"]["seed"]),
                "duration_s": self.duration_s,
                "load_multiplier": float(
                    self.config["workload"].get("load_multiplier", 1.0)
                ),
                "scheduling": self.scheduler.scheduling,
                "mobility_prefetch": self.mobility.prefetch,
            }
        )
        return summary

    def node_statistics(self) -> list[dict]:
        return self.metrics.node_statistics(self.topology.nodes)

    def task_records(self) -> list[dict]:
        rows = []
        for task in self.metrics.window_tasks():
            if not task.completed:
                continue
            row = asdict(task)
            row["latency_ms"] = 1000.0 * task.response_time
            row["deadline_miss"] = not task.met_deadline
            rows.append(row)
        return rows
