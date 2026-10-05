"""
Dynamic MAC Address Table Learning, Forwarding & Aging Simulation Engine.
Implements IEEE 802.1D bridge forwarding/filtering rules.
"""

from dataclasses import dataclass, field
import time
from typing import Dict, List, Optional, Tuple


@dataclass
class MACEntry:
    mac_address: str
    port_id: str
    vlan_id: int
    entry_type: str = "DYNAMIC"  # DYNAMIC or STATIC
    last_seen: float = field(default_factory=time.time)


@dataclass
class SwitchPort:
    port_id: str
    speed_mbps: int = 1000
    is_up: bool = True
    vlan_id: int = 1


class MACTable:
    """Content Addressable Memory (CAM) / MAC Address forwarding table."""

    def __init__(self, aging_time_sec: float = 300.0):
        self.aging_time_sec = aging_time_sec
        # Key: (vlan_id, mac_address) -> MACEntry
        self._entries: Dict[Tuple[int, str], MACEntry] = {}

    def learn(self, mac_address: str, port_id: str, vlan_id: int = 1) -> None:
        """Learn or refresh source MAC binding to port within a VLAN."""
        clean_mac = mac_address.lower().strip()
        key = (vlan_id, clean_mac)
        self._entries[key] = MACEntry(
            mac_address=clean_mac,
            port_id=port_id,
            vlan_id=vlan_id,
            entry_type="DYNAMIC",
            last_seen=time.time(),
        )

    def lookup(self, mac_address: str, vlan_id: int = 1) -> Optional[str]:
        """Lookup destination port for MAC address. Returns port_id or None (flood)."""
        self.age_out()
        clean_mac = mac_address.lower().strip()
        key = (vlan_id, clean_mac)
        entry = self._entries.get(key)
        if entry:
            return entry.port_id
        return None

    def age_out(self, current_time: Optional[float] = None) -> int:
        """Purge entries older than aging_time_sec. Returns count of purged entries."""
        now = current_time if current_time is not None else time.time()
        expired = [
            k for k, v in self._entries.items()
            if v.entry_type == "DYNAMIC" and (now - v.last_seen) > self.aging_time_sec
        ]
        for k in expired:
            del self._entries[k]
        return len(expired)

    def get_all_entries(self) -> List[MACEntry]:
        """Return list of all active MAC entries."""
        self.age_out()
        return list(self._entries.values())


class Switch:
    """Simulated L2 Ethernet Switch forwarding engine."""

    def __init__(self, switch_name: str, ports: List[str]):
        self.switch_name = switch_name
        self.ports = {p: SwitchPort(port_id=p) for p in ports}
        self.mac_table = MACTable()

    def process_frame(
        self,
        ingress_port: str,
        src_mac: str,
        dst_mac: str,
        vlan_id: int = 1
    ) -> Tuple[str, List[str]]:
        """
        Process an incoming Ethernet frame.
        1. Learn source MAC on ingress port.
        2. Lookup destination MAC.
        3. If broadcast (FF:FF:FF:FF:FF:FF) or unknown unicast -> Flood to all ports in VLAN except ingress.
        4. If known unicast -> Forward only to destination port.
        Returns: (action, egress_ports)
        """
        if ingress_port not in self.ports or not self.ports[ingress_port].is_up:
            raise ValueError(f"Port {ingress_port} is invalid or down")

        # Step 1: Learn Source MAC
        self.mac_table.learn(src_mac, ingress_port, vlan_id)

        clean_dst = dst_mac.lower().strip()
        is_broadcast = (clean_dst in ("ff:ff:ff:ff:ff:ff", "ffff.ffff.ffff"))

        if is_broadcast:
            egress = [p for p in self.ports.keys() if p != ingress_port and self.ports[p].is_up]
            return ("FLOOD_BROADCAST", egress)

        dest_port = self.mac_table.lookup(clean_dst, vlan_id)
        if dest_port and dest_port in self.ports and self.ports[dest_port].is_up:
            if dest_port == ingress_port:
                return ("FILTER_DROP", [])  # Frame arrived on same port as destination
            return ("FORWARD_UNICAST", [dest_port])
        else:
            # Unknown unicast flooding
            egress = [p for p in self.ports.keys() if p != ingress_port and self.ports[p].is_up]
            return ("FLOOD_UNKNOWN_UNICAST", egress)
