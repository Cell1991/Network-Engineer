"""Unit tests for Binary Packet Dissectors, Checksums, and TCP State Machine."""

import pytest
from src.packets.checksum import calculate_internet_checksum, verify_internet_checksum
from src.packets.frame import EthernetFrame
from src.packets.ipv4 import IPv4Packet
from src.packets.ipv6 import IPv6Packet
from src.packets.tcp import TCPSegment, TCPFlags, TCPConnectionStateMachine, TCPState
from src.packets.udp import UDPDatagram
from src.packets.icmp import ICMPPacket, ICMPType


def test_rfc1071_checksum():
    # Standard RFC test buffer
    data = b"\x45\x00\x00\x3c\x1c\x46\x40\x00\x40\x06\x00\x00\xac\x10\x0a\x63\xac\x10\x0a\x0c"
    chksum = calculate_internet_checksum(data)
    assert chksum > 0

    # Inject checksum at offset 10-11
    data_with_chk = data[:10] + chksum.to_bytes(2, "big") + data[12:]
    assert verify_internet_checksum(data_with_chk) is True


def test_ethernet_frame_serialization_roundtrip():
    payload = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    frame = EthernetFrame(
        dst_mac="00:11:22:33:44:55",
        src_mac="66:77:88:99:aa:bb",
        ethertype=0x0800,
        payload=payload,
        vlan_id=100
    )
    raw = frame.serialize()
    parsed = EthernetFrame.parse(raw)

    assert parsed.dst_mac == "00:11:22:33:44:55"
    assert parsed.src_mac == "66:77:88:99:aa:bb"
    assert parsed.ethertype == 0x0800
    assert parsed.vlan_id == 100
    assert parsed.payload == payload


def test_ipv4_and_tcp_serialization():
    tcp = TCPSegment(
        src_port=12345,
        dst_port=80,
        seq_num=100,
        ack_num=0,
        flags=TCPFlags.SYN,
        payload=b""
    )
    tcp_raw = tcp.serialize("192.168.1.10", "93.184.216.34")
    parsed_tcp = TCPSegment.parse(tcp_raw)
    assert parsed_tcp.src_port == 12345
    assert parsed_tcp.dst_port == 80
    assert parsed_tcp.flags == TCPFlags.SYN

    ip = IPv4Packet(
        src_ip="192.168.1.10",
        dst_ip="93.184.216.34",
        protocol=6,
        payload=tcp_raw
    )
    ip_raw = ip.serialize()
    parsed_ip = IPv4Packet.parse(ip_raw)
    assert parsed_ip.src_ip == "192.168.1.10"
    assert parsed_ip.dst_ip == "93.184.216.34"
    assert parsed_ip.protocol == 6


def test_tcp_fsm_transitions():
    fsm = TCPConnectionStateMachine()
    assert fsm.state == TCPState.CLOSED

    assert fsm.handle_event("OPEN_ACTIVE") == TCPState.SYN_SENT
    assert fsm.handle_event("RECV_SYN_ACK") == TCPState.ESTABLISHED
    assert fsm.handle_event("SEND_FIN") == TCPState.FIN_WAIT_1
    assert fsm.handle_event("RECV_ACK") == TCPState.FIN_WAIT_2
    assert fsm.handle_event("RECV_FIN") == TCPState.TIME_WAIT
    assert fsm.handle_event("TIMEOUT_2MSL") == TCPState.CLOSED


def test_icmp_ping_packet():
    icmp = ICMPPacket(
        type=ICMPType.ECHO_REQUEST,
        code=0,
        payload=b"abcdefghijklmnopqrstuvwabcdefghi",
        identifier=0x1234,
        sequence_number=1
    )
    raw = icmp.serialize()
    parsed = ICMPPacket.parse(raw)
    assert parsed.type == ICMPType.ECHO_REQUEST
    assert parsed.identifier == 0x1234
    assert parsed.sequence_number == 1
    assert parsed.payload == b"abcdefghijklmnopqrstuvwabcdefghi"
