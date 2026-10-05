"""Unit tests for OSPF Dijkstra SPF, BGP Path Selection, and Radix LPM."""

import pytest
from src.routing.dijkstra_ospf import OSPFNetwork, LinkStateRouter
from src.routing.bellman_ford_rip import RIPNetwork, RIPRouter
from src.routing.bgp_engine import BGPRoutingEngine, BGPRoute, BGPOrigin, PeeringType
from src.routing.routing_table import RadixRoutingTable, RouteEntry


def test_dijkstra_ospf_spf():
    net = OSPFNetwork()
    r1 = LinkStateRouter("R1")
    r2 = LinkStateRouter("R2")
    r3 = LinkStateRouter("R3")
    r4 = LinkStateRouter("R4")

    net.add_router(r1)
    net.add_router(r2)
    net.add_router(r3)
    net.add_router(r4)

    # Topology:
    # R1 --(10)-- R2 --(10)-- R4
    #  |                      |
    # (50)                   (10)
    #  |                      |
    # R3 --------(10)---------+
    net.connect("R1", "R2", cost_1_to_2=10, cost_2_to_1=10)
    net.connect("R2", "R4", cost_1_to_2=10, cost_2_to_1=10)
    net.connect("R1", "R3", cost_1_to_2=50, cost_2_to_1=50)
    net.connect("R3", "R4", cost_1_to_2=10, cost_2_to_1=10)

    spf = net.calculate_spf("R1")

    # Shortest path to R4 should be R1 -> R2 -> R4 (cost 20) rather than R1 -> R3 -> R4 (cost 60)
    assert spf["R4"].total_cost == 20
    assert spf["R4"].next_hops == ["R2"]
    assert spf["R4"].full_path == ["R1", "R2", "R4"]


def test_bgp_best_path_selection():
    # Candidate 1: Local Pref 200, AS-Path [65001, 65002]
    r1 = BGPRoute("10.0.0.0/8", "1.1.1.1", "1.1.1.1", "1.1.1.1", PeeringType.EBGP, local_pref=200, as_path=[65001, 65002])
    # Candidate 2: Local Pref 100, AS-Path [65003] (Shorter AS path, but lower Local Pref)
    r2 = BGPRoute("10.0.0.0/8", "2.2.2.2", "2.2.2.2", "2.2.2.2", PeeringType.EBGP, local_pref=100, as_path=[65003])

    winner, log = BGPRoutingEngine.select_best_path([r1, r2])
    assert winner.next_hop == "1.1.1.1"  # Local Pref wins before AS-Path

    # Now test equal Local Pref, AS-Path tiebreaker
    r3 = BGPRoute("10.0.0.0/8", "3.3.3.3", "3.3.3.3", "3.3.3.3", PeeringType.EBGP, local_pref=100, as_path=[65001, 65002])
    r4 = BGPRoute("10.0.0.0/8", "4.4.4.4", "4.4.4.4", "4.4.4.4", PeeringType.EBGP, local_pref=100, as_path=[65003])
    winner2, log2 = BGPRoutingEngine.select_best_path([r3, r4])
    assert winner2.next_hop == "4.4.4.4"  # Shorter AS path wins


def test_radix_longest_prefix_match():
    fib = RadixRoutingTable()
    fib.add_route(RouteEntry(prefix="0.0.0.0/0", next_hop="192.168.1.254", interface_name="eth0"))
    fib.add_route(RouteEntry(prefix="10.0.0.0/8", next_hop="10.1.1.1", interface_name="eth1"))
    fib.add_route(RouteEntry(prefix="10.1.0.0/16", next_hop="10.1.2.1", interface_name="eth2"))
    fib.add_route(RouteEntry(prefix="10.1.5.0/24", next_hop="10.1.5.254", interface_name="eth3"))

    # Destination 10.1.5.42 should match the most specific /24 route (eth3)
    match1 = fib.lookup_lpm("10.1.5.42")
    assert match1 is not None
    assert match1.interface_name == "eth3"
    assert match1.prefix == "10.1.5.0/24"

    # Destination 10.1.20.5 should match /16 route (eth2)
    match2 = fib.lookup_lpm("10.1.20.5")
    assert match2 is not None
    assert match2.interface_name == "eth2"

    # Destination 8.8.8.8 should match default route /0 (eth0)
    match3 = fib.lookup_lpm("8.8.8.8")
    assert match3 is not None
    assert match3.interface_name == "eth0"
