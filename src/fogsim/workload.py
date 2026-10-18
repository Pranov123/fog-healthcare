from __future__ import annotations

import random
from typing import Callable

import simpy

from .entities import Patient, TaskClassSpec


def spawn_patients(count: int, zone_count: int, rng: random.Random) -> list[Patient]:
    return [Patient(patient_id=i, zone=rng.randrange(zone_count)) for i in range(count)]


def task_stream(
    env: simpy.Environment,
    rng: random.Random,
    patient: Patient,
    spec: TaskClassSpec,
    rate_per_patient: float,
    emit: Callable,
) -> simpy.events.Process:
    """Poisson stream of one task class for one patient."""

    def _run():
        if rate_per_patient <= 0:
            return
        while True:
            yield env.timeout(rng.expovariate(rate_per_patient))
            emit(patient, spec)

    return env.process(_run())
