"""Unit tests for L2 Switching, MAC Table, STP, and VLAN tagging."""

import pytest
from src.switching.mac_table import Switch, MACTable
from src.switching.stp import STPNetwork, SpanningTreeBridge, PortRole, PortState
from src.switching.vlan import VLANFrame, VLANPort, PortMode


def test_mac_table_learning_and_forwarding():
    sw = Switch("SW-01", ports=["Gi0/1", "Gi0/2", "Gi0/3", "Gi0/4"])

    # Frame from Host A on Gi0/1 to Broadcast
    action, egress = sw.process_frame("Gi0/1", "00:00:00:00:00:01", "ff:ff:ff:ff:ff:ff")
    assert action == "FLOOD_BROADCAST"
    assert sorted(egress) == ["Gi0/2", "Gi0/3", "Gi0/4"]

    # Frame from Host B on Gi0/2 to Host A
    action, egress = sw.process_frame("Gi0/2", "00:00:00:00:00:02", "00:00:00:00:00:01")
    assert action == "FORWARD_UNICAST"
    assert egress == ["Gi0/1"]

    # Unknown unicast flooding
    action, egress = sw.process_frame("Gi0/1", "00:00:00:00:00:01", "00:00:00:00:00:99")
    assert action == "FLOOD_UNKNOWN_UNICAST"
    assert sorted(egress) == ["Gi0/2", "Gi0/3", "Gi0/4"]


def test_stp_triangle_convergence():
    net = STPNetwork()
    sw1 = SpanningTreeBridge("SW1", priority=4096, mac_address="00:00:00:00:00:01")
    sw1.add_port("P1", speed_mbps=1000)
    sw1.add_port("P2", speed_mbps=1000)

    sw2 = SpanningTreeBridge("SW2", priority=32768, mac_address="00:00:00:00:00:02")
    sw2.add_port("P1", speed_mbps=1000)
    sw2.add_port("P2", speed_mbps=1000)

    sw3 = SpanningTreeBridge("SW3", priority=32768, mac_address="00:00:00:00:00:03")
    sw3.add_port("P1", speed_mbps=1000)
    sw3.add_port("P2", speed_mbps=1000)

    net.add_bridge(sw1)
    net.add_bridge(sw2)
    net.add_bridge(sw3)

    net.connect("SW1", "P1", "SW2", "P1")
    net.connect("SW2", "P2", "SW3", "P1")
    net.connect("SW3", "P2", "SW1", "P2")

    root = net.converge()
    assert root == "SW1"
    assert sw1.is_root_bridge() is True

    # Root Bridge all ports DESIGNATED / FORWARDING
    assert sw1.ports["P1"].role == PortRole.DESIGNATED
    assert sw1.ports["P2"].role == PortRole.DESIGNATED

    # Exactly one port in the triangle loop must be BLOCKING / ALTERNATE
    all_ports = [
        sw1.ports["P1"], sw1.ports["P2"],
        sw2.ports["P1"], sw2.ports["P2"],
        sw3.ports["P1"], sw3.ports["P2"]
    ]
    blocking_ports = [p for p in all_ports if p.state == PortState.BLOCKING]
    assert len(blocking_ports) == 1
    assert blocking_ports[0].role == PortRole.ALTERNATE


def test_vlan_access_and_trunk_ports():
    acc_port = VLANPort("Gi0/1", mode=PortMode.ACCESS, access_vlan=10)
    trunk_port = VLANPort("Gi0/24", mode=PortMode.TRUNK, native_vlan=1, allowed_vlans={1, 10, 20})

    # Host sends untagged frame to access port
    frame_in = VLANFrame(src_mac="00:11:22:33:44:55", dst_mac="00:aa:bb:cc:dd:ee", payload=b"hello")
    tagged_internal = acc_port.process_ingress(frame_in)
    assert tagged_internal is not None
    assert tagged_internal.vlan_id == 10

    # Internal tagged frame egresses trunk port
    trunk_out = trunk_port.process_egress(tagged_internal)
    assert trunk_out is not None
    assert trunk_out.vlan_id == 10

    # Trunk receives tagged frame on VLAN 20
    trunk_in = trunk_port.process_ingress(VLANFrame("00:11:22:33:44:55", "00:aa:bb:cc:dd:ee", b"data", vlan_id=20))
    assert trunk_in is not None
    assert trunk_in.vlan_id == 20

    # Trunk rejects disallowed VLAN 99
    trunk_in_bad = trunk_port.process_ingress(VLANFrame("00:11:22:33:44:55", "00:aa:bb:cc:dd:ee", b"data", vlan_id=99))
    assert trunk_in_bad is None
