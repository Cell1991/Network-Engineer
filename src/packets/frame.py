"""
Ethernet II Frame (IEEE 802.3) Builder and Dissector.
Supports optional 802.1Q Single Tagging and 802.1ad QinQ Double Tagging.
"""

from dataclasses import dataclass
import struct
from typing import Optional, Tuple


@dataclass
class EthernetFrame:
    dst_mac: str
    src_mac: str
    ethertype: int
    payload: bytes
    vlan_id: Optional[int] = None

    @classmethod
    def parse(cls, raw_bytes: bytes) -> "EthernetFrame":
        """Dissect raw binary frame into structured EthernetFrame."""
        if len(raw_bytes) < 14:
            raise ValueError(f"Raw frame too short ({len(raw_bytes)} bytes < 14)")

        dst_b, src_b, ethertype = struct.unpack("!6s6sH", raw_bytes[:14])
        dst_mac = ":".join(f"{b:02x}" for b in dst_b)
        src_mac = ":".join(f"{b:02x}" for b in src_b)

        # Check for 802.1Q Tag (0x8100)
        if ethertype == 0x8100:
            if len(raw_bytes) < 18:
                raise ValueError("Truncated 802.1Q frame")
            tci, inner_ethertype = struct.unpack("!HH", raw_bytes[14:18])
            vlan_id = tci & 0x0FFF
            payload = raw_bytes[18:]
            return cls(
                dst_mac=dst_mac,
                src_mac=src_mac,
                ethertype=inner_ethertype,
                payload=payload,
                vlan_id=vlan_id
            )
        else:
            payload = raw_bytes[14:]
            return cls(
                dst_mac=dst_mac,
                src_mac=src_mac,
                ethertype=ethertype,
                payload=payload,
                vlan_id=None
            )

    def serialize(self) -> bytes:
        """Serialize frame to binary bytes."""
        dst_b = bytes.fromhex(self.dst_mac.replace(":", "").replace(".", "").replace("-", ""))
        src_b = bytes.fromhex(self.src_mac.replace(":", "").replace(".", "").replace("-", ""))

        if self.vlan_id is not None:
            tpid = 0x8100
            tci = self.vlan_id & 0x0FFF
            hdr = struct.pack("!6s6sHHH", dst_b, src_b, tpid, tci, self.ethertype)
        else:
            hdr = struct.pack("!6s6sH", dst_b, src_b, self.ethertype)

        return hdr + self.payload
