"""
TCP Segment (RFC 793 / RFC 9293) Builder, Dissector & State Machine.
Supports TCP pseudo-header checksum, control flags (URG, ACK, PSH, RST, SYN, FIN),
window sizing, and state transitions.
"""

from dataclasses import dataclass
from enum import Enum
import struct
from typing import Optional, Tuple
from .checksum import calculate_internet_checksum, verify_internet_checksum


class TCPFlags(int):
    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    PSH = 0x08
    ACK = 0x10
    URG = 0x20
    ECE = 0x40
    CWR = 0x80


class TCPState(str, Enum):
    CLOSED = "CLOSED"
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT_1 = "FIN_WAIT_1"
    FIN_WAIT_2 = "FIN_WAIT_2"
    CLOSE_WAIT = "CLOSE_WAIT"
    CLOSING = "CLOSING"
    LAST_ACK = "LAST_ACK"
    TIME_WAIT = "TIME_WAIT"


@dataclass
class TCPSegment:
    src_port: int
    dst_port: int
    seq_num: int
    ack_num: int
    flags: int
    payload: bytes
    window_size: int = 65535
    urgent_pointer: int = 0
    checksum: Optional[int] = None

    @classmethod
    def parse(cls, raw_bytes: bytes) -> "TCPSegment":
        """Dissect raw bytes into TCPSegment."""
        if len(raw_bytes) < 20:
            raise ValueError(f"Raw TCP segment too short ({len(raw_bytes)} bytes < 20)")

        src_p, dst_p, seq, ack, offset_flags, win, chksum, urg = struct.unpack("!HHIIHHHH", raw_bytes[:20])
        data_offset = (offset_flags >> 12) & 0xF
        flags = offset_flags & 0x1FF

        hdr_len = data_offset * 4
        payload = raw_bytes[hdr_len:]

        return cls(
            src_port=src_p,
            dst_port=dst_p,
            seq_num=seq,
            ack_num=ack,
            flags=flags,
            payload=payload,
            window_size=win,
            urgent_pointer=urg,
            checksum=chksum
        )

    def serialize(self, src_ip: Optional[str] = None, dst_ip: Optional[str] = None) -> bytes:
        """
        Serialize TCP segment into binary bytes.
        If src_ip and dst_ip are provided, compute RFC 793 IPv4 Pseudo-Header Checksum.
        """
        data_offset = 5  # 20 bytes header
        offset_flags = (data_offset << 12) | (self.flags & 0x1FF)

        # Build header with 0 checksum
        hdr_no_chk = struct.pack(
            "!HHIIHHHH",
            self.src_port,
            self.dst_port,
            self.seq_num,
            self.ack_num,
            offset_flags,
            self.window_size,
            0,
            self.urgent_pointer
        )

        segment_data = hdr_no_chk + self.payload

        if src_ip and dst_ip:
            # Build IPv4 Pseudo-Header
            src_b = bytes([int(x) for x in src_ip.split(".")])
            dst_b = bytes([int(x) for x in dst_ip.split(".")])
            proto = 6  # TCP
            tcp_len = len(segment_data)
            pseudo_hdr = struct.pack("!4s4sBBH", src_b, dst_b, 0, proto, tcp_len)
            calc_chk = calculate_internet_checksum(pseudo_hdr + segment_data)
        else:
            calc_chk = calculate_internet_checksum(segment_data)

        # Re-pack header with calculated checksum
        hdr = struct.pack(
            "!HHIIHHHH",
            self.src_port,
            self.dst_port,
            self.seq_num,
            self.ack_num,
            offset_flags,
            self.window_size,
            calc_chk,
            self.urgent_pointer
        )

        return hdr + self.payload


class TCPConnectionStateMachine:
    """Tracks RFC 793 / RFC 9293 TCP state transitions."""

    def __init__(self, initial_state: TCPState = TCPState.CLOSED):
        self.state = initial_state
        self.seq_num = 1000
        self.ack_num = 0

    def handle_event(self, event: str) -> TCPState:
        """
        Process connection event or segment flag arrival.
        Events: 'OPEN_ACTIVE', 'OPEN_PASSIVE', 'SEND_SYN', 'RECV_SYN',
                'RECV_SYN_ACK', 'SEND_ACK', 'SEND_FIN', 'RECV_FIN', 'TIMEOUT_2MSL'
        """
        transitions = {
            (TCPState.CLOSED, "OPEN_PASSIVE"): TCPState.LISTEN,
            (TCPState.CLOSED, "OPEN_ACTIVE"): TCPState.SYN_SENT,
            (TCPState.LISTEN, "RECV_SYN"): TCPState.SYN_RECEIVED,
            (TCPState.SYN_SENT, "RECV_SYN_ACK"): TCPState.ESTABLISHED,
            (TCPState.SYN_SENT, "RECV_SYN"): TCPState.SYN_RECEIVED,
            (TCPState.SYN_RECEIVED, "RECV_ACK"): TCPState.ESTABLISHED,
            (TCPState.ESTABLISHED, "SEND_FIN"): TCPState.FIN_WAIT_1,
            (TCPState.ESTABLISHED, "RECV_FIN"): TCPState.CLOSE_WAIT,
            (TCPState.FIN_WAIT_1, "RECV_ACK"): TCPState.FIN_WAIT_2,
            (TCPState.FIN_WAIT_1, "RECV_FIN"): TCPState.CLOSING,
            (TCPState.FIN_WAIT_2, "RECV_FIN"): TCPState.TIME_WAIT,
            (TCPState.CLOSE_WAIT, "SEND_FIN"): TCPState.LAST_ACK,
            (TCPState.LAST_ACK, "RECV_ACK"): TCPState.CLOSED,
            (TCPState.CLOSING, "RECV_ACK"): TCPState.TIME_WAIT,
            (TCPState.TIME_WAIT, "TIMEOUT_2MSL"): TCPState.CLOSED,
        }

        next_st = transitions.get((self.state, event))
        if next_st is None:
            raise ValueError(f"Illegal TCP transition: event '{event}' in state '{self.state.value}'")
        self.state = next_st
        return self.state
