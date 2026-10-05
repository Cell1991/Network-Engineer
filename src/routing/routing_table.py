"""
Radix Tree / Trie Longest Prefix Match (LPM) Forwarding Information Base (FIB).
Provides O(W) forwarding lookup where W=32 for IPv4.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from ..subnetting.calculator import IPv4Calculator


@dataclass
class RouteEntry:
    prefix: str  # e.g. "10.0.0.0/8"
    next_hop: str
    interface_name: str
    admin_distance: int = 1
    metric: int = 0


class TrieNode:
    """Node in binary radix forwarding trie."""
    def __init__(self):
        self.children: Dict[int, TrieNode] = {}  # 0 or 1
        self.route: Optional[RouteEntry] = None


class RadixRoutingTable:
    """Forwarding Information Base with Longest Prefix Match."""

    def __init__(self):
        self.root = TrieNode()
        self.total_routes = 0

    def add_route(self, route: RouteEntry) -> None:
        """Insert prefix into radix trie."""
        info = IPv4Calculator.calculate(route.prefix)
        net_int = IPv4Calculator.ip_to_int(info.network_address)
        prefix_len = info.cidr_prefix

        curr = self.root
        for i in range(31, 31 - prefix_len, -1):
            bit = (net_int >> i) & 1
            if bit not in curr.children:
                curr.children[bit] = TrieNode()
            curr = curr.children[bit]

        curr.route = route
        self.total_routes += 1

    def lookup_lpm(self, ip_address: str) -> Optional[RouteEntry]:
        """
        Perform Longest Prefix Match (LPM) for a destination IP.
        Traverse down tree; record the deepest matching route found.
        """
        ip_int = IPv4Calculator.ip_to_int(ip_address)
        curr = self.root
        best_match: Optional[RouteEntry] = curr.route

        for i in range(31, -1, -1):
            bit = (ip_int >> i) & 1
            if bit not in curr.children:
                break
            curr = curr.children[bit]
            if curr.route is not None:
                best_match = curr.route

        return best_match
