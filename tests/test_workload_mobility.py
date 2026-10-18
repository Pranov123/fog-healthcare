import random

import simpy

from fogsim.config import load_config
from fogsim.entities import build_task_classes
from fogsim.mobility import MobilityManager
from fogsim.topology import Topology
from fogsim.workload import spawn_patients, task_stream


def test_patient_generation_and_stream():
    cfg = load_config()
    env = simpy.Environment()
    rng = random.Random(1)
    patients = spawn_patients(10, cfg["topology"]["num_fog_nodes"], rng)
    assert len(patients) == 10
    assert all(0 <= p.zone < cfg["topology"]["num_fog_nodes"] for p in patients)

    specs = build_task_classes(cfg)
    emitted = []
    for patient in patients:
        task_stream(env, rng, patient, specs["critical"], rate_per_patient=0.5, emit=lambda p, s: emitted.append((p, s)))
    env.run(until=100)
    assert 430 < len(emitted) < 570


def test_prefetch_reduces_handoff_blocking():
    cfg = load_config()
    cfg["mobility"]["enabled"] = True
    env = simpy.Environment()
    rng = random.Random(2)
    topo = Topology(env, cfg)
    patient = spawn_patients(1, topo.num_fog, rng)[0]
    patient.zone = 0

    plain = MobilityManager(env, rng, topo, cfg, prefetch=False)
    prefetch = MobilityManager(env, rng, topo, cfg, prefetch=True)
    base = plain.move(patient, 1)
    fast = prefetch.move(patient, 1)

    assert base.transfer_s > 0
    assert fast.blocking_s < base.blocking_s
    assert base.successful is False
    assert fast.successful is True
    assert patient.zone == 1
    assert patient.handoffs == 2
