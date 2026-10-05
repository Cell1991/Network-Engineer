"""
Multi-Vendor Network Configuration Template Engine.
Generates structured configuration commands for Cisco IOS-XE, Junos, and Arista EOS.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InterfaceConfig:
    name: str
    description: str
    ipv4_address: Optional[str] = None  # e.g. "192.168.1.1/24"
    ipv6_address: Optional[str] = None  # e.g. "2001:db8::1/64"
    vlan_id: Optional[int] = None
    is_trunk: bool = False
    mtu: int = 1500
    enabled: bool = True


@dataclass
class BGPConfig:
    local_as: int
    router_id: str
    neighbors: List[dict]  # {"ip": "...", "remote_as": ..., "description": "..."}
    networks: List[str]    # ["10.0.0.0/24", ...]


class NetworkTemplateEngine:
    """Renders multi-vendor configuration payloads."""

    @staticmethod
    def render_cisco_ios(interfaces: List[InterfaceConfig], bgp: Optional[BGPConfig] = None) -> str:
        """Render Cisco IOS-XE syntax."""
        lines = ["!", "! Cisco IOS-XE Configuration", "!"]
        for iface in interfaces:
            lines.append(f"interface {iface.name}")
            lines.append(f" description {iface.description}")
            if iface.mtu != 1500:
                lines.append(f" mtu {iface.mtu}")
            if iface.ipv4_address:
                parts = iface.ipv4_address.split("/")
                ip = parts[0]
                prefix = int(parts[1]) if len(parts) > 1 else 24
                # Convert prefix to mask
                mask_int = ((1 << prefix) - 1) << (32 - prefix) if prefix > 0 else 0
                mask = f"{(mask_int >> 24) & 0xFF}.{(mask_int >> 16) & 0xFF}.{(mask_int >> 8) & 0xFF}.{mask_int & 0xFF}"
                lines.append(f" ip address {ip} {mask}")
            if iface.ipv6_address:
                lines.append(f" ipv6 address {iface.ipv6_address}")
            if iface.is_trunk:
                lines.append(" switchport mode trunk")
            elif iface.vlan_id:
                lines.append(f" switchport access vlan {iface.vlan_id}")
                lines.append(" switchport mode access")
            if iface.enabled:
                lines.append(" no shutdown")
            else:
                lines.append(" shutdown")
            lines.append("!")

        if bgp:
            lines.append(f"router bgp {bgp.local_as}")
            lines.append(f" bgp router-id {bgp.router_id}")
            for net in bgp.networks:
                ip, pfx = net.split("/")
                mask_int = ((1 << int(pfx)) - 1) << (32 - int(pfx)) if int(pfx) > 0 else 0
                mask = f"{(mask_int >> 24) & 0xFF}.{(mask_int >> 16) & 0xFF}.{(mask_int >> 8) & 0xFF}.{mask_int & 0xFF}"
                lines.append(f" network {ip} mask {mask}")
            for nbr in bgp.neighbors:
                lines.append(f" neighbor {nbr['ip']} remote-as {nbr['remote_as']}")
                if "description" in nbr:
                    lines.append(f" neighbor {nbr['ip']} description {nbr['description']}")
            lines.append("!")

        return "\n".join(lines)

    @staticmethod
    def render_junos(interfaces: List[InterfaceConfig], bgp: Optional[BGPConfig] = None) -> str:
        """Render Juniper Junos syntax."""
        lines = ["# Juniper Junos Configuration", "interfaces {"]
        for iface in interfaces:
            lines.append(f"    {iface.name} {{")
            lines.append(f"        description \"{iface.description}\";")
            lines.append("        unit 0 {")
            lines.append("            family inet {")
            if iface.ipv4_address:
                lines.append(f"                address {iface.ipv4_address};")
            lines.append("            }")
            lines.append("        }")
            lines.append("    }")
        lines.append("}")

        if bgp:
            lines.append("protocols {")
            lines.append("    bgp {")
            lines.append(f"        group OVERLAY-PEERS {{")
            lines.append(f"            type external;")
            for nbr in bgp.neighbors:
                lines.append(f"            neighbor {nbr['ip']} {{")
                lines.append(f"                peer-as {nbr['remote_as']};")
                lines.append("            }")
            lines.append("        }")
            lines.append("    }")
            lines.append("}")

        return "\n".join(lines)
