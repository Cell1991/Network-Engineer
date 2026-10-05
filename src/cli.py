"""
Network Engineering Interactive CLI Suite.
Provides command-line utilities for subnet calculations, VLSM allocation,
supernet aggregation, OSPF SPF calculation, BGP path selection,
STP bridge convergence, packet crafting & config diffing.

STRICT CONFORMANCE: ZERO EMOJIS.
"""

import argparse
import sys
from typing import List

from .subnetting.calculator import IPv4Calculator
from .subnetting.vlsm import VLSMPlanner
from .subnetting.supernet import SupernetAggregator
from .subnetting.ipv6_tools import IPv6Tools
from .routing.dijkstra_ospf import OSPFNetwork, LinkStateRouter
from .routing.bgp_engine import BGPRoutingEngine, BGPRoute, BGPOrigin, PeeringType
from .switching.stp import STPNetwork, SpanningTreeBridge
from .packets.ipv4 import IPv4Packet
from .packets.tcp import TCPSegment, TCPFlags
from .automation.config_differ import NetworkConfigDiffer


def print_banner():
    banner = """
================================================================================
  NETWORK ENGINEER COMPENDIUM & SIMULATION SUITE
  Protocol Engine // Algorithmic Routing // Packet Dissector // NetDevOps
================================================================================
"""
    print(banner)


def cmd_subnet(args):
    print(f"\n[+] Analyzing IPv4 Target: {args.target}")
    info = IPv4Calculator.calculate(args.target)
    print("--------------------------------------------------------------------------------")
    print(f"  IP Address          : {info.ip_address} (/{info.cidr_prefix})")
    print(f"  Subnet Mask         : {info.netmask}")
    print(f"  Wildcard Mask       : {info.wildcard_mask}")
    print(f"  Network Address     : {info.network_address}")
    print(f"  Broadcast Address   : {info.broadcast_address}")
    print(f"  Usable Host Range   : {info.first_usable_ip} -> {info.last_usable_ip}")
    print(f"  Total Addresses     : {info.total_hosts:,}")
    print(f"  Usable Host Count   : {info.usable_hosts:,}")
    print(f"  Classful Category   : {info.ip_class}")
    print(f"  RFC 1918 Private    : {'YES' if info.is_private_rfc1918 else 'NO'}")
    print(f"  IP Binary           : {info.ip_binary}")
    print(f"  Mask Binary         : {info.netmask_binary}")
    print("--------------------------------------------------------------------------------\n")


def cmd_vlsm(args):
    print(f"\n[+] Executing VLSM Optimal Partition on Base Block: {args.base}")
    reqs = []
    for item in args.requirements.split(","):
        if ":" in item:
            name, count = item.split(":")
            reqs.append((name.strip(), int(count.strip())))
        else:
            reqs.append((f"Subnet_{len(reqs)+1}", int(item.strip())))

    allocations = VLSMPlanner.allocate(args.base, reqs)
    print("--------------------------------------------------------------------------------")
    print(f"  {'SUBNET NAME':<18} | {'REQ':<6} | {'ALLOC':<6} | {'CIDR':<18} | {'USABLE RANGE':<32}")
    print("--------------------------------------------------------------------------------")
    for a in allocations:
        cidr_str = f"{a.network_address}/{a.cidr_prefix}"
        range_str = f"{a.first_usable_ip} - {a.last_usable_ip}"
        print(f"  {a.name:<18} | {a.required_hosts:<6} | {a.usable_hosts:<6} | {cidr_str:<18} | {range_str:<32}")
    print("--------------------------------------------------------------------------------\n")


def cmd_summarize(args):
    print(f"\n[+] Computing CIDR Route Aggregation for: {args.networks}")
    nets = [n.strip() for n in args.networks.split(",")]
    supernet = SupernetAggregator.summarize(nets)
    print("--------------------------------------------------------------------------------")
    print(f"  Input Subnets Count : {len(nets)}")
    print(f"  Optimal Supernet    : {supernet}")
    print("--------------------------------------------------------------------------------\n")


def cmd_ipv6_eui64(args):
    print(f"\n[+] Generating Modified EUI-64 & SLAAC from MAC: {args.mac}")
    eui64 = IPv6Tools.mac_to_eui64(args.mac)
    slaac_ll = IPv6Tools.generate_slaac_link_local(args.mac)
    print("--------------------------------------------------------------------------------")
    print(f"  Source MAC Address  : {args.mac}")
    print(f"  Interface ID (64-b) : {eui64}")
    print(f"  SLAAC Link-Local    : {slaac_ll}")
    if args.prefix:
        global_slaac = IPv6Tools.generate_slaac_global(args.prefix, args.mac)
        print(f"  SLAAC Global Unicast: {global_slaac} (Prefix: {args.prefix})")
    print("--------------------------------------------------------------------------------\n")


def cmd_stp_sim(args):
    print("\n[+] Initializing 3-Bridge Spanning Tree Protocol (IEEE 802.1D) Topology...")
    net = STPNetwork()
    
    # Create 3 switches in a triangle (which creates a physical switching loop)
    sw1 = SpanningTreeBridge("SW-01", priority=4096, mac_address="00:11:22:33:44:01")
    sw1.add_port("Gi0/1", speed_mbps=1000)
    sw1.add_port("Gi0/2", speed_mbps=1000)

    sw2 = SpanningTreeBridge("SW-02", priority=32768, mac_address="00:11:22:33:44:02")
    sw2.add_port("Gi0/1", speed_mbps=1000)
    sw2.add_port("Gi0/2", speed_mbps=1000)

    sw3 = SpanningTreeBridge("SW-03", priority=32768, mac_address="00:11:22:33:44:03")
    sw3.add_port("Gi0/1", speed_mbps=1000)
    sw3.add_port("Gi0/2", speed_mbps=1000)

    net.add_bridge(sw1)
    net.add_bridge(sw2)
    net.add_bridge(sw3)

    # Interconnect: SW1-Gi0/1 <-> SW2-Gi0/1, SW2-Gi0/2 <-> SW3-Gi0/1, SW3-Gi0/2 <-> SW1-Gi0/2
    net.connect("SW-01", "Gi0/1", "SW-02", "Gi0/1")
    net.connect("SW-02", "Gi0/2", "SW-03", "Gi0/1")
    net.connect("SW-03", "Gi0/2", "SW-01", "Gi0/2")

    root_name = net.converge()

    print("--------------------------------------------------------------------------------")
    print(f"  ELECTED ROOT BRIDGE : {root_name} (Priority {net.bridges[root_name].priority})")
    print("--------------------------------------------------------------------------------")
    for b_name, b in net.bridges.items():
        is_root = " [ROOT]" if b.is_root_bridge() else ""
        print(f"  Bridge {b.bridge_name}{is_root} (Root Path Cost = {b.root_path_cost}):")
        for p_name, p in b.ports.items():
            print(f"    - Port {p_name:<6} : Role = {p.role.value:<12} | State = {p.state.value}")
    print("--------------------------------------------------------------------------------\n")


def cmd_bgp_sim(args):
    print("\n[+] Evaluating BGP-4 Best Path Selection for Prefix 198.51.100.0/24...")
    r1 = BGPRoute(
        prefix="198.51.100.0/24",
        next_hop="203.0.113.1",
        peer_ip="203.0.113.1",
        peer_router_id="1.1.1.1",
        peering_type=PeeringType.EBGP,
        weight=0,
        local_pref=100,
        as_path=[65001, 65002],
        origin=BGPOrigin.IGP,
        med=50
    )
    r2 = BGPRoute(
        prefix="198.51.100.0/24",
        next_hop="198.51.100.2",
        peer_ip="198.51.100.2",
        peer_router_id="2.2.2.2",
        peering_type=PeeringType.EBGP,
        weight=0,
        local_pref=100,
        as_path=[65003],  # Shorter AS-Path
        origin=BGPOrigin.IGP,
        med=100
    )

    winner, steps = BGPRoutingEngine.select_best_path([r1, r2])

    print("--------------------------------------------------------------------------------")
    print("  BGP DECISION LOG PIPELINE:")
    for s in steps:
        print(f"  [STEP {s.step_number:02d}] {s.step_name:<16} : {s.reason}")
        print(f"     Surviving   : {s.surviving_candidates}")
        print(f"     Eliminated  : {s.eliminated_candidates}")
    print("--------------------------------------------------------------------------------")
    print(f"  WINNING ROUTE       : Next-Hop {winner.next_hop} via AS-PATH {winner.as_path}")
    print("--------------------------------------------------------------------------------\n")


def cmd_packet_craft(args):
    print(f"\n[+] Crafting Raw Binary IPv4 + TCP Segment (SYN)...")
    tcp_seg = TCPSegment(
        src_port=54321,
        dst_port=443,
        seq_num=1000,
        ack_num=0,
        flags=TCPFlags.SYN,
        payload=b""
    )
    tcp_raw = tcp_seg.serialize(src_ip="10.0.0.1", dst_ip="10.0.0.2")

    ip_pkt = IPv4Packet(
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        protocol=6,  # TCP
        payload=tcp_raw
    )
    ip_raw = ip_pkt.serialize()

    print("--------------------------------------------------------------------------------")
    print(f"  Serialized Packet Size : {len(ip_raw)} bytes")
    print(f"  IPv4 Header Checksum   : 0x{ip_pkt.checksum if ip_pkt.checksum else 0:04x}")
    print(f"  Raw Hex Dump           : {ip_raw.hex()}")
    print("--------------------------------------------------------------------------------\n")


def main():
    parser = argparse.ArgumentParser(
        prog="network-engineer",
        description="Network Engineering Architecture & Simulation Suite (Zero Emojis)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Operational Subcommands")

    # Subnet command
    p_subnet = subparsers.add_parser("subnet", help="Calculate IPv4 Subnet Metrics")
    p_subnet.add_argument("target", help="IP/CIDR address (e.g. 192.168.1.1/24)")

    # VLSM command
    p_vlsm = subparsers.add_parser("vlsm", help="Variable Length Subnet Mask Allocator")
    p_vlsm.add_argument("base", help="Base Network block (e.g. 10.0.0.0/24)")
    p_vlsm.add_argument("requirements", help="Comma-separated host counts (e.g. Sales:50,Dev:25,WAN:2)")

    # Summarize command
    p_sum = subparsers.add_parser("summarize", help="CIDR Route Summarization Engine")
    p_sum.add_argument("networks", help="Comma-separated CIDR blocks (e.g. 192.168.0.0/24,192.168.1.0/24)")

    # IPv6 EUI-64 command
    p_eui64 = subparsers.add_parser("ipv6-eui64", help="Modified EUI-64 Identifier & SLAAC Generator")
    p_eui64.add_argument("mac", help="MAC address (e.g. 00:1A:2B:3C:4D:5E)")
    p_eui64.add_argument("--prefix", help="Optional /64 Global Unicast Prefix")

    # STP Simulation command
    subparsers.add_parser("stp-sim", help="Simulate Spanning Tree Bridge Root Election")

    # BGP Simulation command
    subparsers.add_parser("bgp-sim", help="Simulate BGP-4 Best Path Decision Engine")

    # Packet Craft command
    subparsers.add_parser("packet-craft", help="Craft & serialize raw binary IPv4/TCP frame")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        return

    print_banner()
    if args.command == "subnet":
        cmd_subnet(args)
    elif args.command == "vlsm":
        cmd_vlsm(args)
    elif args.command == "summarize":
        cmd_summarize(args)
    elif args.command == "ipv6-eui64":
        cmd_ipv6_eui64(args)
    elif args.command == "stp-sim":
        cmd_stp_sim(args)
    elif args.command == "bgp-sim":
        cmd_bgp_sim(args)
    elif args.command == "packet-craft":
        cmd_packet_craft(args)


if __name__ == "__main__":
    main()
