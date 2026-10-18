import pytest
import simpy

from fogsim.config import load_config
from fogsim.energy import node_energy
from fogsim.topology import Link, Topology


def test_link_delay_and_energy():
    env = simpy.Environment()
    link = Link(env, "test", bandwidth_mbps=1000, latency_ms=3, energy_j_per_mb=1.0)
    assert link.tx_time(1024) == pytest.approx(1024 * 8 / 1000 / 1000 + 0.003)
    assert link.energy(1024) == pytest.approx(1.0)


def test_topology_paths():
    cfg = load_config()
    env = simpy.Environment()
    topo = Topology(env, cfg)
    assert len(topo.fogs) == cfg["topology"]["num_fog_nodes"]
    assert topo.path(0, topo.fogs[0]) == [topo.edge_links[0]]
    assert topo.path(0, topo.fogs[1]) == [topo.edge_links[0], topo.backbone[(0, 1)]]
    assert topo.path(0, topo.cloud) == [topo.edge_links[0], topo.wan]
    assert topo.path_delay(0, topo.fogs[0], 100) > 0


def test_node_energy_model():
    cfg = load_config()
    env = simpy.Environment()
    topo = Topology(env, cfg)
    fog = topo.fogs[0]
    # half utilization for 100 s: 35 W idle + 75 W * 0.5 = 72.5 W average
    assert node_energy(fog, 100.0, fog.cores * 50.0) == pytest.approx(7250.0)
    cloud = topo.cloud
    assert node_energy(cloud, 100.0, cloud.cores * 50.0) == pytest.approx(13000.0)
