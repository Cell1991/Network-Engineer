"""
IPv4 Packet (RFC 791) Header Builder and Dissector.
Supports Bitwise Flag fields (DF, MF), Fragment Offset, DSCP/ECN, TTL, and Checksum validation.
"""

from dataclasses import dataclass
import struct
from typing import Optional, Tuple
from .checksum import calculate_internet_checksum, verify_internet_checksum
from ..subnetting.calculator import IPv4Calculator


@dataclass
class IPv4Packet:
    src_ip: str
    dst_ip: str
    protocol: int  # 6=TCP, 17=UDP, 1=ICMP, 89=OSPF
    payload: bytes
    ttl: int = 64
    dscp: int = 0
    ecn: int = 0
    identification: int = 0x1234
    df_flag: bool = True   # Don't Fragment
    mf_flag: bool = False  # More Fragments
    fragment_offset: int = 0
    checksum: Optional[int] = None

    @classmethod
    def parse(cls, raw_bytes: bytes) -> "IPv4Packet":
        """Dissect raw bytes into IPv4Packet object."""
        if len(raw_bytes) < 20:
            raise ValueError(f"Raw IPv4 packet too short ({len(raw_bytes)} bytes < 20)")

        v_ihl, tos, total_len, ident, flags_frag, ttl, proto, chksum = struct.unpack("!BBHHHBBH", raw_bytes[:12])
        version = (v_ihl >> 4) & 0xF
        ihl = v_ihl & 0xF
        if version != 4:
            raise ValueError(f"Invalid IP version {version} (expected 4)")
        if ihl < 5:
            raise ValueError(f"Invalid IHL {ihl} (minimum 5)")

        dscp = (tos >> 2) & 0x3F
        ecn = tos & 0x03

        df = bool(flags_frag & 0x4000)
        mf = bool(flags_frag & 0x2000)
        frag_offset = flags_frag & 0x1FFF

        src_ip_b, dst_ip_b = struct.unpack("!4s4s", raw_bytes[12:20])
        src_ip = ".".join(str(b) for b in src_ip_b)
        dst_ip = ".".join(str(b) for b in dst_ip_b)

        hdr_len = ihl * 4
        # Verify header checksum
        is_valid = verify_internet_checksum(raw_bytes[:hdr_len])
        if not is_valid:
            raise ValueError(f"IPv4 Header Checksum mismatch: 0x{chksum:04x}")

        payload = raw_bytes[hdr_len:total_len]
        return cls(
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=proto,
            payload=payload,
            ttl=ttl,
            dscp=dscp,
            ecn=ecn,
            identification=ident,
            df_flag=df,
            mf_flag=mf,
            fragment_offset=frag_offset,
            checksum=chksum
        )

    def serialize(self) -> bytes:
        """Serialize IPv4 packet into binary with calculated RFC 1071 header checksum."""
        version = 4
        ihl = 5  # 20 bytes standard header
        v_ihl = (version << 4) | ihl
        tos = ((self.dscp & 0x3F) << 2) | (self.ecn & 0x03)
        total_len = 20 + len(self.payload)

        flags_frag = 0
        if self.df_flag:
            flags_frag |= 0x4000
        if self.mf_flag:
            flags_frag |= 0x2000
        flags_frag |= (self.fragment_offset & 0x1FFF)

        src_b = bytes([int(x) for x in self.src_ip.split(".")])
        dst_b = bytes([int(x) for x in self.dst_ip.split(".")])

        # Pack header with 0 checksum for calculation
        hdr_no_chk = struct.pack(
            "!BBHHHBBH4s4s",
            v_ihl, tos, total_len, self.identification,
            flags_frag, self.ttl, self.protocol, 0,
            src_b, dst_b
        )

        calc_chk = calculate_internet_checksum(hdr_no_chk)

        hdr = struct.pack(
            "!BBHHHBBH4s4s",
            v_ihl, tos, total_len, self.identification,
            flags_frag, self.ttl, self.protocol, calc_chk,
            src_b, dst_b
        )

        return hdr + self.payload
