"""
OSPF Link-State Routing & Dijkstra's Shortest Path First (SPF) Simulator.
Calculates Shortest Path Trees (SPT), ECMP (Equal-Cost Multi-Path) routes,
and Link-State Database (LSDB) convergence.
"""

from dataclasses import dataclass, field
import heapq
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Link:
    neighbor_router_id: str
    interface_ip: str
    cost: int
    bandwidth_mbps: int = 1000


@dataclass
class SPFResult:
    destination_router_id: str
    total_cost: int
    next_hops: List[str]  # Multi-path support
    full_path: List[str]


class LinkStateRouter:
    """Represents an OSPF Router with Link State Advertisements (LSAs)."""

    def __init__(self, router_id: str):
        self.router_id = router_id
        # Links: neighbor_id -> Link
        self.links: Dict[str, Link] = {}

    def add_link(
        self,
        neighbor_id: str,
        interface_ip: str,
        cost: Optional[int] = None,
        bandwidth_mbps: int = 1000,
        reference_bw_mbps: int = 100000
    ) -> None:
        """
        Calculate OSPF Cost = Reference Bandwidth / Interface Bandwidth (min 1).
        Default Reference Bandwidth: 100 Gbps (100000 Mbps).
        """
        if cost is None:
            calc_cost = max(1, reference_bw_mbps // max(1, bandwidth_mbps))
        else:
            calc_cost = cost
        
        self.links[neighbor_id] = Link(
            neighbor_router_id=neighbor_id,
            interface_ip=interface_ip,
            cost=calc_cost,
            bandwidth_mbps=bandwidth_mbps
        )


class OSPFNetwork:
    """Link-State Database (LSDB) and Dijkstra SPF Engine."""

    def __init__(self):
        self.routers: Dict[str, LinkStateRouter] = {}

    def add_router(self, router: LinkStateRouter) -> None:
        self.routers[router.router_id] = router

    def connect(
        self,
        r1_id: str,
        r2_id: str,
        cost_1_to_2: Optional[int] = None,
        cost_2_to_1: Optional[int] = None,
        bandwidth_mbps: int = 1000
    ) -> None:
        """Add bidirectional OSPF link between two routers."""
        r1 = self.routers[r1_id]
        r2 = self.routers[r2_id]
        r1.add_link(r2_id, f"10.0.0.{len(r1.links)+1}", cost=cost_1_to_2, bandwidth_mbps=bandwidth_mbps)
        r2.add_link(r1_id, f"10.0.0.{len(r2.links)+1}", cost=cost_2_to_1, bandwidth_mbps=bandwidth_mbps)

    def calculate_spf(self, source_router_id: str) -> Dict[str, SPFResult]:
        """
        Execute Dijkstra's algorithm from `source_router_id` to all destinations in LSDB.
        Returns mapping: destination_router_id -> SPFResult
        """
        if source_router_id not in self.routers:
            raise ValueError(f"Source router '{source_router_id}' does not exist in LSDB")

        # Distances: router_id -> min_cost
        distances: Dict[str, int] = {r_id: float("inf") for r_id in self.routers}
        distances[source_router_id] = 0

        # Predecessors: router_id -> list of predecessor router_ids (to reconstruct paths and ECMP)
        predecessors: Dict[str, List[str]] = {r_id: [] for r_id in self.routers}

        # Priority Queue: (cost, router_id)
        pq: List[Tuple[int, str]] = [(0, source_router_id)]
        visited: Set[str] = set()

        while pq:
            curr_cost, curr_node = heapq.heappop(pq)
            if curr_node in visited:
                continue
            visited.add(curr_node)

            curr_router = self.routers[curr_node]
            for nbr_id, link in curr_router.links.items():
                if nbr_id not in self.routers:
                    continue
                new_cost = curr_cost + link.cost
                if new_cost < distances[nbr_id]:
                    distances[nbr_id] = new_cost
                    predecessors[nbr_id] = [curr_node]
                    heapq.heappush(pq, (new_cost, nbr_id))
                elif new_cost == distances[nbr_id]:
                    # ECMP tie
                    if curr_node not in predecessors[nbr_id]:
                        predecessors[nbr_id].append(curr_node)

        # Build results
        results: Dict[str, SPFResult] = {}

        def get_all_paths(node: str) -> List[List[str]]:
            if node == source_router_id:
                return [[source_router_id]]
            paths = []
            for pred in predecessors[node]:
                for p in get_all_paths(pred):
                    paths.append(p + [node])
            return paths

        for dest_id in self.routers:
            if dest_id == source_router_id:
                results[dest_id] = SPFResult(
                    destination_router_id=dest_id,
                    total_cost=0,
                    next_hops=[source_router_id],
                    full_path=[source_router_id]
                )
                continue

            if distances[dest_id] == float("inf"):
                continue

            paths = get_all_paths(dest_id)
            # Find next-hops from paths (the second element in each path)
            next_hops = list(set(p[1] for p in paths if len(p) > 1))
            best_path = paths[0] if paths else []

            results[dest_id] = SPFResult(
                destination_router_id=dest_id,
                total_cost=distances[dest_id],
                next_hops=sorted(next_hops),
                full_path=best_path
            )

        return results
