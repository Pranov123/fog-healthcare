import pytest

from fogsim.config import load_config
from fogsim.simulator import FogSimulation

ALGORITHMS = ["cloud_only", "fog_rr", "fog_ll", "fog_edf", "proposed"]


def make_config(algorithm: str, **overrides):
    base = {
        "simulation": {"duration_s": 300, "warmup_s": 20, "seed": 7},
        "workload": {"num_patients": 40, "load_multiplier": 1.0},
        "mobility": {"enabled": False},
        "algorithm": {"name": algorithm},
    }
    for section, values in overrides.items():
        if section in base and isinstance(values, dict):
            base[section].update(values)
        else:
            base[section] = values
    return load_config(overrides=base)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_every_algorithm_produces_metrics(algorithm):
    sim = FogSimulation(make_config(algorithm))
    summary = sim.run()
    assert summary["tasks_arrived"] > 100
    assert summary["tasks_completed"] > 0
    assert 0.0 <= summary["tcr_pct"] <= 100.0
    assert summary["mean_latency_ms"] > 0
    assert summary["energy_j"] > 0
    assert 0.0 <= summary["jain_index"] <= 1.0
    assert len(sim.node_statistics()) == summary["fog_nodes"] + 1
    assert len(sim.task_records()) == summary["tasks_completed"]


def test_simulation_is_deterministic():
    first = FogSimulation(make_config("proposed")).run()
    second = FogSimulation(make_config("proposed")).run()
    for key in ("tasks_arrived", "tasks_met", "mean_latency_ms", "energy_j", "tcr_pct"):
        assert first[key] == second[key]


def test_cloud_only_executes_everything_in_cloud():
    summary = FogSimulation(make_config("cloud_only")).run()
    assert summary["cloud_share_pct"] == pytest.approx(100.0)
    assert summary["fog_share_pct"] == pytest.approx(0.0)


def test_proposed_uses_fog_for_critical_traffic():
    sim = FogSimulation(make_config("proposed"))
    sim.run()
    critical = [r for r in sim.task_records() if r["task_class"] == "critical"]
    assert critical
    fog_critical = [r for r in critical if r["tier"] == "fog"]
    assert len(fog_critical) / len(critical) > 0.9


def test_critical_latency_below_batch_latency():
    summary = FogSimulation(make_config("proposed")).run()
    assert summary["critical_mean_ms"] < summary["batch_mean_ms"]
