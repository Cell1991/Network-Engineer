"""
UDP Datagram (RFC 768) Builder and Dissector.
Supports 8-byte UDP header with source port, dest port, length, and pseudo-header checksum.
"""

from dataclasses import dataclass
import struct
from typing import Optional
from .checksum import calculate_internet_checksum


@dataclass
class UDPDatagram:
    src_port: int
    dst_port: int
    payload: bytes
    checksum: Optional[int] = None

    @classmethod
    def parse(cls, raw_bytes: bytes) -> "UDPDatagram":
        """Dissect raw bytes into UDPDatagram."""
        if len(raw_bytes) < 8:
            raise ValueError(f"Raw UDP datagram too short ({len(raw_bytes)} bytes < 8)")

        src_p, dst_p, length, chksum = struct.unpack("!HHHH", raw_bytes[:8])
        payload = raw_bytes[8:length]

        return cls(
            src_port=src_p,
            dst_port=dst_p,
            payload=payload,
            checksum=chksum
        )

    def serialize(self, src_ip: Optional[str] = None, dst_ip: Optional[str] = None) -> bytes:
        """Serialize UDP datagram to binary bytes."""
        length = 8 + len(self.payload)
        hdr_no_chk = struct.pack("!HHHH", self.src_port, self.dst_port, length, 0)
        data = hdr_no_chk + self.payload

        if src_ip and dst_ip:
            src_b = bytes([int(x) for x in src_ip.split(".")])
            dst_b = bytes([int(x) for x in dst_ip.split(".")])
            proto = 17  # UDP
            pseudo_hdr = struct.pack("!4s4sBBH", src_b, dst_b, 0, proto, length)
            calc_chk = calculate_internet_checksum(pseudo_hdr + data)
        else:
            calc_chk = 0

        hdr = struct.pack("!HHHH", self.src_port, self.dst_port, length, calc_chk)
        return hdr + self.payload
