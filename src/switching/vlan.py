"""
IEEE 802.1Q VLAN Tagging & Port Simulation Engine.
Models 802.1Q 4-byte header tag (TPID 0x8100, PCP, DEI, VID),
Access ports, Trunk ports, and Native VLAN stripping.
"""

from dataclasses import dataclass
from enum import Enum
import struct
from typing import List, Optional, Set, Tuple


class PortMode(str, Enum):
    ACCESS = "ACCESS"
    TRUNK = "TRUNK"


@dataclass
class VLANFrame:
    src_mac: str
    dst_mac: str
    payload: bytes
    ethertype: int = 0x0800  # IPv4
    vlan_id: Optional[int] = None  # None = untagged, 1-4094 = tagged
    pcp: int = 0  # Priority Code Point (0-7)
    dei: int = 0  # Drop Eligible Indicator (0 or 1)

    def serialize(self) -> bytes:
        """Serialize frame into binary bytes (with or without 802.1Q tag)."""
        dst_b = bytes.fromhex(self.dst_mac.replace(":", "").replace(".", "").replace("-", ""))
        src_b = bytes.fromhex(self.src_mac.replace(":", "").replace(".", "").replace("-", ""))

        if self.vlan_id is not None:
            # Insert 4-byte 802.1Q header: TPID (0x8100), TCI (PCP 3b + DEI 1b + VID 12b)
            tpid = 0x8100
            tci = ((self.pcp & 0x07) << 13) | ((self.dei & 0x01) << 12) | (self.vlan_id & 0x0FFF)
            hdr = struct.pack("!6s6sHHH", dst_b, src_b, tpid, tci, self.ethertype)
        else:
            hdr = struct.pack("!6s6sH", dst_b, src_b, self.ethertype)

        return hdr + self.payload


class VLANPort:
    """Switchport with Access or Trunk configuration."""

    def __init__(
        self,
        port_id: str,
        mode: PortMode = PortMode.ACCESS,
        access_vlan: int = 1,
        native_vlan: int = 1,
        allowed_vlans: Optional[Set[int]] = None
    ):
        self.port_id = port_id
        self.mode = mode
        self.access_vlan = access_vlan
        self.native_vlan = native_vlan
        self.allowed_vlans: Set[int] = allowed_vlans if allowed_vlans is not None else {1}

    def process_ingress(self, frame: VLANFrame) -> Optional[VLANFrame]:
        """
        Process incoming frame on switchport.
        - On ACCESS port: Untagged frame is assigned `access_vlan`. Tagged frame is dropped.
        - On TRUNK port: Untagged frame is assigned `native_vlan`. Tagged frame is checked against `allowed_vlans`.
        """
        if self.mode == PortMode.ACCESS:
            if frame.vlan_id is not None and frame.vlan_id != self.access_vlan:
                # Ingress tagged frame on access port with mismatched tag is dropped
                return None
            return VLANFrame(
                src_mac=frame.src_mac,
                dst_mac=frame.dst_mac,
                payload=frame.payload,
                ethertype=frame.ethertype,
                vlan_id=self.access_vlan,
                pcp=frame.pcp,
                dei=frame.dei
            )

        elif self.mode == PortMode.TRUNK:
            assigned_vid = frame.vlan_id if frame.vlan_id is not None else self.native_vlan
            if assigned_vid not in self.allowed_vlans:
                return None  # VLAN not allowed on trunk
            return VLANFrame(
                src_mac=frame.src_mac,
                dst_mac=frame.dst_mac,
                payload=frame.payload,
                ethertype=frame.ethertype,
                vlan_id=assigned_vid,
                pcp=frame.pcp,
                dei=frame.dei
            )

    def process_egress(self, frame: VLANFrame) -> Optional[VLANFrame]:
        """
        Process outgoing frame leaving switchport.
        - On ACCESS port: Tag is stripped (frame egresses untagged).
        - On TRUNK port: If frame VID == native_vlan, tag is stripped. Otherwise, egresses tagged.
        """
        if self.mode == PortMode.ACCESS:
            if frame.vlan_id != self.access_vlan:
                return None  # Frame belongs to different VLAN
            return VLANFrame(
                src_mac=frame.src_mac,
                dst_mac=frame.dst_mac,
                payload=frame.payload,
                ethertype=frame.ethertype,
                vlan_id=None,  # Untagged
                pcp=0,
                dei=0
            )

        elif self.mode == PortMode.TRUNK:
            if frame.vlan_id not in self.allowed_vlans:
                return None  # VLAN not permitted
            
            # If native VLAN, strip tag
            egress_vid = None if frame.vlan_id == self.native_vlan else frame.vlan_id
            return VLANFrame(
                src_mac=frame.src_mac,
                dst_mac=frame.dst_mac,
                payload=frame.payload,
                ethertype=frame.ethertype,
                vlan_id=egress_vid,
                pcp=frame.pcp,
                dei=frame.dei
            )
