from __future__ import annotations

import simpy

from .entities import ComputeNode


class Link:
    """A store-and-forward link with serialized transmission and an energy cost."""

    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        bandwidth_mbps: float,
        latency_ms: float,
        energy_j_per_mb: float,
        parallel: int = 2,
    ) -> None:
        self.env = env
        self.name = name
        self.bandwidth_mbps = float(bandwidth_mbps)
        self.latency_ms = float(latency_ms)
        self.energy_j_per_mb = float(energy_j_per_mb)
        self.resource = simpy.Resource(env, capacity=parallel)
        self.bytes_sent = 0.0
        self.transmissions = 0

    def tx_time(self, size_kb: float) -> float:
        return size_kb * 8.0 / 1000.0 / self.bandwidth_mbps + self.latency_ms / 1000.0

    def energy(self, size_kb: float) -> float:
        return size_kb / 1024.0 * self.energy_j_per_mb


class Topology:
    """Three-tier topology: edge zones -> fog ring -> cloud."""

    def __init__(self, env: simpy.Environment, config: dict) -> None:
        self.env = env
        topo = config["topology"]
        self.num_fog = int(topo["num_fog_nodes"])
        fog_cfg = topo["fog"]
        cloud_cfg = topo["cloud"]
        link_cfg = topo["links"]
        edge_cfg = topo.get("edge", {})

        self.fogs = [
            ComputeNode(
                node_id=i,
                kind="fog",
                zone=i,
                speed_mcycles=float(fog_cfg["cpu_mcycles_per_s"]),
                cores=int(fog_cfg["cores"]),
                mem_mb=float(fog_cfg["mem_mb"]),
                p_idle_w=float(fog_cfg["p_idle_w"]),
                p_busy_w=float(fog_cfg["p_busy_w"]),
            )
            for i in range(self.num_fog)
        ]
        self.cloud = ComputeNode(
            node_id=self.num_fog,
            kind="cloud",
            zone=-1,
            speed_mcycles=float(cloud_cfg["cpu_mcycles_per_s"]),
            cores=int(cloud_cfg["cores"]),
            mem_mb=float(cloud_cfg["mem_mb"]),
            p_idle_w=float(cloud_cfg["p_idle_w"]),
            p_busy_w=float(cloud_cfg["p_busy_w"]),
        )
        self.nodes = self.fogs + [self.cloud]
        self.edge_processing_s = float(edge_cfg.get("processing_latency_ms", 0.0)) / 1000.0

        self.edge_links = [
            Link(
                env,
                f"edge-fog-{i}",
                link_cfg["edge_to_fog_mbps"],
                link_cfg["edge_to_fog_latency_ms"],
                link_cfg["edge_to_fog_energy_j_per_mb"],
                parallel=2,
            )
            for i in range(self.num_fog)
        ]
        self.backbone = {
            (i, j): Link(
                env,
                f"fog-{i}-fog-{j}",
                link_cfg["fog_to_fog_mbps"],
                link_cfg["fog_to_fog_latency_ms"],
                link_cfg["fog_to_fog_energy_j_per_mb"],
                parallel=2,
            )
            for i in range(self.num_fog)
            for j in range(self.num_fog)
            if i != j
        }
        self.wan = Link(
            env,
            "fog-cloud",
            link_cfg["fog_to_cloud_mbps"],
            link_cfg["fog_to_cloud_latency_ms"],
            link_cfg["fog_to_cloud_energy_j_per_mb"],
            parallel=4,
        )

    def node(self, node_id: int) -> ComputeNode:
        if node_id == self.cloud.node_id:
            return self.cloud
        return self.fogs[node_id]

    def neighbors(self, fog_id: int) -> list[int]:
        if self.num_fog < 2:
            return []
        return sorted({(fog_id - 1) % self.num_fog, (fog_id + 1) % self.num_fog})

    def path(self, zone: int, dest: ComputeNode) -> list[Link]:
        zone = zone % self.num_fog
        if dest.kind == "cloud":
            return [self.edge_links[zone], self.wan]
        if dest.zone == zone:
            return [self.edge_links[zone]]
        return [self.edge_links[zone], self.backbone[(zone, dest.zone)]]

    def path_delay(self, zone: int, dest: ComputeNode, size_kb: float) -> float:
        return self.edge_processing_s + sum(link.tx_time(size_kb) for link in self.path(zone, dest))

    def path_energy(self, zone: int, dest: ComputeNode, size_kb: float) -> float:
        return sum(link.energy(size_kb) for link in self.path(zone, dest))
