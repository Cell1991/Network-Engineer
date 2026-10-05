"""
Spanning Tree Protocol (IEEE 802.1D / 802.1w Rapid Spanning Tree) Convergence Simulator.
Simulates Root Bridge election, Root Path Cost (RPC) accumulation,
Root Port (RP), Designated Port (DP), and Alternate/Blocking Port (AP/BP) determinations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set


class PortRole(str, Enum):
    ROOT = "ROOT"
    DESIGNATED = "DESIGNATED"
    ALTERNATE = "ALTERNATE"
    BACKUP = "BACKUP"
    DISABLED = "DISABLED"


class PortState(str, Enum):
    BLOCKING = "BLOCKING"
    LISTENING = "LISTENING"
    LEARNING = "LEARNING"
    FORWARDING = "FORWARDING"
    DISABLED = "DISABLED"


# IEEE 802.1D / 802.1w Standard Port Costs
STANDARD_PORT_COSTS = {
    10: 100,       # 10 Mbps
    100: 19,       # 100 Mbps (FastEthernet)
    1000: 4,       # 1 Gbps (GigabitEthernet)
    10000: 2,      # 10 Gbps (TenGigabitEthernet)
    100000: 1,     # 100 Gbps
}


@dataclass
class BPDU:
    """Bridge Protocol Data Unit."""
    root_bridge_id: Tuple[int, str]  # (priority, mac_address)
    root_path_cost: int
    transmitting_bridge_id: Tuple[int, str]
    transmitting_port_id: str


@dataclass
class STPPort:
    port_name: str
    speed_mbps: int = 1000
    cost: int = 4
    role: PortRole = PortRole.DESIGNATED
    state: PortState = PortState.FORWARDING
    connected_to_bridge: Optional[str] = None
    connected_to_port: Optional[str] = None


class SpanningTreeBridge:
    """Simulated IEEE 802.1D Spanning Tree Bridge."""

    def __init__(self, bridge_name: str, priority: int, mac_address: str):
        self.bridge_name = bridge_name
        self.priority = priority
        self.mac_address = mac_address.lower().strip()
        self.bridge_id: Tuple[int, str] = (self.priority, self.mac_address)
        
        # State
        self.root_bridge_id: Tuple[int, str] = self.bridge_id
        self.root_path_cost: int = 0
        self.root_port: Optional[str] = None
        self.ports: Dict[str, STPPort] = {}

    def add_port(self, port_name: str, speed_mbps: int = 1000, cost: Optional[int] = None) -> None:
        actual_cost = cost if cost is not None else STANDARD_PORT_COSTS.get(speed_mbps, 4)
        self.ports[port_name] = STPPort(
            port_name=port_name,
            speed_mbps=speed_mbps,
            cost=actual_cost,
        )

    def is_root_bridge(self) -> bool:
        return self.root_bridge_id == self.bridge_id


class STPNetwork:
    """Multi-bridge topology convergence solver."""

    def __init__(self):
        self.bridges: Dict[str, SpanningTreeBridge] = {}
        # Links: tuple (b1, p1, b2, p2)
        self.links: List[Tuple[str, str, str, str]] = []

    def add_bridge(self, bridge: SpanningTreeBridge) -> None:
        self.bridges[bridge.bridge_name] = bridge

    def connect(self, b1_name: str, p1_name: str, b2_name: str, p2_name: str) -> None:
        """Connect two bridge ports with a bidirectional link."""
        b1 = self.bridges[b1_name]
        b2 = self.bridges[b2_name]
        
        b1.ports[p1_name].connected_to_bridge = b2_name
        b1.ports[p1_name].connected_to_port = p2_name

        b2.ports[p2_name].connected_to_bridge = b1_name
        b2.ports[p2_name].connected_to_port = p1_name

        self.links.append((b1_name, p1_name, b2_name, p2_name))

    def converge(self) -> str:
        """
        Run STP convergence algorithm.
        1. Elect Root Bridge: Lowest Bridge ID (Priority then MAC).
        2. Determine Root Path Cost (RPC) & Root Port for every non-root bridge.
        3. Determine Designated Port (DP) and Alternate/Blocking Port (AP) per segment.
        Returns elected Root Bridge name.
        """
        if not self.bridges:
            raise ValueError("No bridges configured in STP network")

        # Step 1: Root Bridge Election (Global lowest Bridge ID)
        root_bridge = min(self.bridges.values(), key=lambda b: b.bridge_id)
        root_id = root_bridge.bridge_id

        for b in self.bridges.values():
            b.root_bridge_id = root_id

        # Step 2: Calculate Shortest Path to Root Bridge (Dijkstra on link costs)
        # Distances to root
        distances: Dict[str, int] = {b_name: float("inf") for b_name in self.bridges}
        distances[root_bridge.bridge_name] = 0
        best_root_port: Dict[str, Optional[str]] = {b_name: None for b_name in self.bridges}

        visited: Set[str] = set()
        while len(visited) < len(self.bridges):
            # Pick node with min distance
            unvisited = {b: d for b, d in distances.items() if b not in visited}
            if not unvisited:
                break
            curr_b_name = min(unvisited, key=unvisited.get)
            curr_dist = distances[curr_b_name]
            visited.add(curr_b_name)

            curr_b = self.bridges[curr_b_name]
            for p_name, port in curr_b.ports.items():
                nbr_name = port.connected_to_bridge
                if nbr_name and nbr_name not in visited:
                    link_cost = port.cost
                    new_dist = curr_dist + link_cost
                    if new_dist < distances[nbr_name]:
                        distances[nbr_name] = new_dist
                        # The neighbor's port facing us is its root port candidate
                        best_root_port[nbr_name] = port.connected_to_port
                    elif new_dist == distances[nbr_name]:
                        # Tiebreak on sender's Bridge ID
                        curr_best_p = best_root_port[nbr_name]
                        curr_best_nbr_bridge = self.bridges[nbr_name].ports[curr_best_p].connected_to_bridge
                        if self.bridges[curr_b_name].bridge_id < self.bridges[curr_best_nbr_bridge].bridge_id:
                            best_root_port[nbr_name] = port.connected_to_port

        # Apply root path costs and root ports
        for b_name, b in self.bridges.items():
            b.root_path_cost = distances[b_name]
            b.root_port = best_root_port[b_name]

        # Step 3: Assign Port Roles and States
        # For Root Bridge: all ports are DESIGNATED and FORWARDING
        for p in root_bridge.ports.values():
            p.role = PortRole.DESIGNATED
            p.state = PortState.FORWARDING

        # For non-root bridges:
        for b_name, b in self.bridges.items():
            if b_name == root_bridge.bridge_name:
                continue
            for p_name, p in b.ports.items():
                if p_name == b.root_port:
                    p.role = PortRole.ROOT
                    p.state = PortState.FORWARDING

        # For every link (segment), elect Designated Port vs Alternate Port
        for b1_name, p1_name, b2_name, p2_name in self.links:
            b1 = self.bridges[b1_name]
            b2 = self.bridges[b2_name]
            p1 = b1.ports[p1_name]
            p2 = b2.ports[p2_name]

            # If neither is already a ROOT port on its switch, one must be DP and other AP
            if p1.role == PortRole.ROOT and p2.role == PortRole.ROOT:
                continue
            elif p1.role == PortRole.ROOT:
                p2.role = PortRole.DESIGNATED
                p2.state = PortState.FORWARDING
            elif p2.role == PortRole.ROOT:
                p1.role = PortRole.DESIGNATED
                p1.state = PortState.FORWARDING
            else:
                # Compare (RootPathCost, BridgeID, PortID) to elect Designated Port
                tuple1 = (b1.root_path_cost, b1.bridge_id, p1_name)
                tuple2 = (b2.root_path_cost, b2.bridge_id, p2_name)

                if tuple1 < tuple2:
                    p1.role = PortRole.DESIGNATED
                    p1.state = PortState.FORWARDING
                    p2.role = PortRole.ALTERNATE
                    p2.state = PortState.BLOCKING
                else:
                    p2.role = PortRole.DESIGNATED
                    p2.state = PortState.FORWARDING
                    p1.role = PortRole.ALTERNATE
                    p1.state = PortState.BLOCKING

        return root_bridge.bridge_name
