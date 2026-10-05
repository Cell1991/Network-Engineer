"""
ICMP (Internet Control Message Protocol / RFC 792) Builder & Dissector.
Supports Echo Request (Type 8), Echo Reply (Type 0), Destination Unreachable (Type 3),
Time Exceeded (Type 11), Identifier & Sequence numbers with Checksum calculation.
"""

from dataclasses import dataclass
from enum import IntEnum
import struct
from typing import Optional
from .checksum import calculate_internet_checksum, verify_internet_checksum


class ICMPType(IntEnum):
    ECHO_REPLY = 0
    DEST_UNREACHABLE = 3
    SOURCE_QUENCH = 4
    REDIRECT = 5
    ECHO_REQUEST = 8
    TIME_EXCEEDED = 11
    PARAMETER_PROBLEM = 12


@dataclass
class ICMPPacket:
    type: int
    code: int
    payload: bytes
    identifier: int = 1
    sequence_number: int = 1
    checksum: Optional[int] = None

    @classmethod
    def parse(cls, raw_bytes: bytes) -> "ICMPPacket":
        """Dissect raw bytes into ICMPPacket."""
        if len(raw_bytes) < 8:
            raise ValueError(f"Raw ICMP packet too short ({len(raw_bytes)} bytes < 8)")

        # Verify Checksum
        if not verify_internet_checksum(raw_bytes):
            raise ValueError("ICMP checksum verification failed")

        msg_type, code, chksum, ident, seq = struct.unpack("!BBHHH", raw_bytes[:8])
        payload = raw_bytes[8:]

        return cls(
            type=msg_type,
            code=code,
            payload=payload,
            identifier=ident,
            sequence_number=seq,
            checksum=chksum
        )

    def serialize(self) -> bytes:
        """Serialize ICMP packet with computed checksum."""
        hdr_no_chk = struct.pack("!BBHHH", self.type, self.code, 0, self.identifier, self.sequence_number)
        data = hdr_no_chk + self.payload
        calc_chk = calculate_internet_checksum(data)
        hdr = struct.pack("!BBHHH", self.type, self.code, calc_chk, self.identifier, self.sequence_number)
        return hdr + self.payload
