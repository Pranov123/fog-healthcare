import random

import simpy

from fogsim.config import load_config
from fogsim.entities import Patient, Task
from fogsim.orchestration import build_scheduler
from fogsim.topology import Topology


def make_task(deadline_s=0.05, rank=0, cycles=30):
    return Task(
        task_id=1,
        task_class="critical",
        patient_id=1,
        arrival=0.0,
        size_kb=5,
        cycles=cycles,
        deadline_s=deadline_s,
        rank=rank,
        zone=0,
    )


def setup(name="proposed"):
    cfg = load_config()
    env = simpy.Environment()
    topo = Topology(env, cfg)
    patient = Patient(patient_id=1, zone=0)
    return cfg, topo, patient, build_scheduler(name, topo, cfg)


def test_cloud_only_always_selects_cloud():
    cfg, topo, patient, scheduler = setup("cloud_only")
    assert scheduler.scheduling == "fcfs"
    assert scheduler.plan(make_task(), patient) is topo.cloud


def test_round_robin_cycles_through_fog_nodes():
    cfg, topo, patient, scheduler = setup("fog_rr")
    picks = {scheduler.plan(make_task(), patient).node_id for _ in range(10)}
    assert picks == set(range(topo.num_fog))


def test_least_loaded_avoids_backlogged_node():
    cfg, topo, patient, scheduler = setup("fog_ll")
    topo.fogs[0].pending_cycles = 1e9
    chosen = scheduler.plan(make_task(), patient)
    assert chosen.node_id != 0


def test_proposed_routes_critical_task_to_fog():
    cfg, topo, patient, scheduler = setup("proposed")
    chosen = scheduler.plan(make_task(), patient)
    assert chosen.kind == "fog"
    assert scheduler.scheduling == "edf"
    assert scheduler.prefetch is True


def test_proposed_sends_imaging_to_cloud():
    cfg, topo, patient, scheduler = setup("proposed")
    task = Task(
        task_id=2,
        task_class="imaging",
        patient_id=1,
        arrival=0.0,
        size_kb=50000,
        cycles=15000,
        deadline_s=20.0,
        rank=2,
        zone=0,
    )
    assert scheduler.plan(task, patient).kind == "cloud"
