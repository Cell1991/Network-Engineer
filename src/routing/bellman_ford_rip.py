"""
Distance-Vector Routing Protocol (RIPv2 / RFC 2453) Convergence Engine.
Simulates Bellman-Ford algorithm, Hop-Count metric (Infinity = 16),
Split Horizon, and Poison Reverse loop prevention.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class RIPRoute:
    prefix: str
    metric: int  # 1 to 15, 16 is unreachable
    next_hop: str
    learned_from_interface: str


class RIPRouter:
    """RIP Router maintaining routing table and generating distance vectors."""

    def __init__(self, router_id: str):
        self.router_id = router_id
        # Key: prefix -> RIPRoute
        self.routing_table: Dict[str, RIPRoute] = {}
        # Interfaces: interface_name -> (neighbor_router_id, link_cost)
        self.interfaces: Dict[str, Tuple[str, int]] = {}

    def add_direct_network(self, prefix: str, interface_name: str) -> None:
        """Add directly connected network with metric 1."""
        self.routing_table[prefix] = RIPRoute(
            prefix=prefix,
            metric=1,
            next_hop="0.0.0.0",
            learned_from_interface=interface_name
        )

    def add_interface(self, interface_name: str, neighbor_id: str, cost: int = 1) -> None:
        self.interfaces[interface_name] = (neighbor_id, cost)

    def generate_update(self, egress_interface: str, split_horizon_poison: bool = True) -> Dict[str, int]:
        """
        Generate distance vector for sending out `egress_interface`.
        If `split_horizon_poison` is True:
        - If route was learned on this interface, advertise metric 16 (Poison Reverse).
        """
        update: Dict[str, int] = {}
        for prefix, route in self.routing_table.items():
            if split_horizon_poison and route.learned_from_interface == egress_interface:
                update[prefix] = 16  # Poison reverse
            else:
                update[prefix] = route.metric
        return update

    def receive_update(
        self,
        ingress_interface: str,
        sender_id: str,
        advertised_routes: Dict[str, int]
    ) -> bool:
        """
        Process incoming distance vector from neighbor.
        Returns True if routing table changed.
        """
        changed = False
        link_cost = self.interfaces.get(ingress_interface, (None, 1))[1]

        for prefix, advertised_metric in advertised_routes.items():
            new_metric = min(16, advertised_metric + link_cost)
            existing_route = self.routing_table.get(prefix)

            if existing_route is None:
                if new_metric < 16:
                    self.routing_table[prefix] = RIPRoute(
                        prefix=prefix,
                        metric=new_metric,
                        next_hop=sender_id,
                        learned_from_interface=ingress_interface
                    )
                    changed = True
            else:
                # If update comes from the same next-hop, always update metric (even if worse)
                if existing_route.next_hop == sender_id:
                    if existing_route.metric != new_metric:
                        existing_route.metric = new_metric
                        changed = True
                else:
                    # If update from different neighbor has better metric, install it
                    if new_metric < existing_route.metric:
                        self.routing_table[prefix] = RIPRoute(
                            prefix=prefix,
                            metric=new_metric,
                            next_hop=sender_id,
                            learned_from_interface=ingress_interface
                        )
                        changed = True

        return changed


class RIPNetwork:
    """Multi-router RIP network simulation harness."""

    def __init__(self):
        self.routers: Dict[str, RIPRouter] = {}

    def add_router(self, router: RIPRouter) -> None:
        self.routers[router.router_id] = router

    def connect(self, r1_id: str, if1: str, r2_id: str, if2: str, cost: int = 1) -> None:
        r1 = self.routers[r1_id]
        r2 = self.routers[r2_id]
        r1.add_interface(if1, r2_id, cost)
        r2.add_interface(if2, r1_id, cost)

    def converge(self, max_iterations: int = 20, split_horizon_poison: bool = True) -> int:
        """
        Run iterative Bellman-Ford synchronous update rounds until convergence.
        Returns number of iterations to converge.
        """
        for iteration in range(1, max_iterations + 1):
            any_changed = False
            # Collect all outbound updates
            updates_to_deliver = []
            for r_id, router in self.routers.items():
                for if_name, (nbr_id, cost) in router.interfaces.items():
                    vec = router.generate_update(if_name, split_horizon_poison)
                    # Find receiving interface on neighbor
                    nbr = self.routers[nbr_id]
                    nbr_if = next((k for k, v in nbr.interfaces.items() if v[0] == r_id), "eth0")
                    updates_to_deliver.append((nbr_id, nbr_if, r_id, vec))

            # Deliver updates
            for dest_id, dest_if, sender_id, vec in updates_to_deliver:
                ch = self.routers[dest_id].receive_update(dest_if, sender_id, vec)
                if ch:
                    any_changed = True

            if not any_changed:
                return iteration

        return max_iterations
