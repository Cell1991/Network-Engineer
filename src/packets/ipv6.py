"""
IPv6 Packet (RFC 8200) Header Builder and Dissector.
Fixed 40-byte base header: Version, Traffic Class, Flow Label, Payload Length, Next Header, Hop Limit.
"""

from dataclasses import dataclass
import ipaddress
import struct
from typing import Optional


@dataclass
class IPv6Packet:
    src_ip: str
    dst_ip: str
    next_header: int  # 6=TCP, 17=UDP, 58=ICMPv6
    payload: bytes
    traffic_class: int = 0
    flow_label: int = 0
    hop_limit: int = 64

    @classmethod
    def parse(cls, raw_bytes: bytes) -> "IPv6Packet":
        """Dissect raw bytes into IPv6Packet object."""
        if len(raw_bytes) < 40:
            raise ValueError(f"Raw IPv6 packet too short ({len(raw_bytes)} bytes < 40)")

        v_tc_fl, payload_len, next_hdr, hop_limit = struct.unpack("!IHBB", raw_bytes[:8])
        version = (v_tc_fl >> 28) & 0xF
        if version != 6:
            raise ValueError(f"Invalid IPv6 version {version} (expected 6)")

        traffic_class = (v_tc_fl >> 20) & 0xFF
        flow_label = v_tc_fl & 0xFFFFF

        src_b, dst_b = struct.unpack("!16s16s", raw_bytes[8:40])
        src_ip = str(ipaddress.IPv6Address(src_b))
        dst_ip = str(ipaddress.IPv6Address(dst_b))

        payload = raw_bytes[40:40 + payload_len]

        return cls(
            src_ip=src_ip,
            dst_ip=dst_ip,
            next_header=next_hdr,
            payload=payload,
            traffic_class=traffic_class,
            flow_label=flow_label,
            hop_limit=hop_limit
        )

    def serialize(self) -> bytes:
        """Serialize IPv6 packet into 40-byte header + payload."""
        version = 6
        v_tc_fl = ((version & 0xF) << 28) | ((self.traffic_class & 0xFF) << 20) | (self.flow_label & 0xFFFFF)
        payload_len = len(self.payload)

        src_b = ipaddress.IPv6Address(self.src_ip).packed
        dst_b = ipaddress.IPv6Address(self.dst_ip).packed

        hdr = struct.pack("!IHBB16s16s", v_tc_fl, payload_len, self.next_header, self.hop_limit, src_b, dst_b)
        return hdr + self.payload
