"""
IPv6 Addressing, EUI-64 Identifier Generation, and SLAAC Engine.
Compliant with RFC 4291, RFC 5952, and RFC 4862.
"""

import ipaddress
import re
from typing import Tuple


class IPv6Tools:
    """IPv6 Address manipulation, zero-compression, and EUI-64 generation."""

    @staticmethod
    def expand_ipv6(ipv6_str: str) -> str:
        """Expand IPv6 address to full 8-hextet 32-hex-character form."""
        addr = ipaddress.IPv6Address(ipv6_str.strip())
        return addr.exploded

    @staticmethod
    def compress_ipv6(ipv6_str: str) -> str:
        """Compress IPv6 address following RFC 5952 canonical formatting standard."""
        addr = ipaddress.IPv6Address(ipv6_str.strip())
        return addr.compressed

    @staticmethod
    def mac_to_eui64(mac_str: str) -> str:
        """
        Convert 48-bit MAC address into 64-bit Modified EUI-64 Interface Identifier.
        Process:
        1. Split MAC into two 24-bit halves.
        2. Insert 0xFFFE between the halves.
        3. Invert the 7th bit (Universal/Local bit) of the first octet.
        Example: 00:1A:2B:3C:4D:5E -> 021a:2bff:fe3c:4d5e
        """
        # Clean MAC
        clean_mac = re.sub(r"[^0-9a-fA-F]", "", mac_str.strip())
        if len(clean_mac) != 12:
            raise ValueError(f"Invalid MAC address '{mac_str}': must have 12 hex digits")

        octets = [int(clean_mac[i:i+2], 16) for i in range(0, 12, 2)]

        # Invert 7th bit (bit 1 of octet 0, counting from LSB 0: bit 1 is 0x02)
        octets[0] ^= 0x02

        # Form 8 octets: [0, 1, 2, 0xFF, 0xFE, 3, 4, 5]
        eui64_octets = [
            octets[0], octets[1], octets[2],
            0xFF, 0xFE,
            octets[3], octets[4], octets[5]
        ]

        hextets = [
            f"{(eui64_octets[0] << 8) | eui64_octets[1]:04x}",
            f"{(eui64_octets[2] << 8) | eui64_octets[3]:04x}",
            f"{(eui64_octets[4] << 8) | eui64_octets[5]:04x}",
            f"{(eui64_octets[6] << 8) | eui64_octets[7]:04x}",
        ]

        return ":".join(hextets)

    @classmethod
    def generate_slaac_link_local(cls, mac_str: str) -> str:
        """Generate RFC 4862 Link-Local IPv6 address (fe80::/64) using EUI-64."""
        eui64 = cls.mac_to_eui64(mac_str)
        raw_addr = f"fe80::{eui64}"
        return cls.compress_ipv6(raw_addr)

    @classmethod
    def generate_slaac_global(cls, prefix_64: str, mac_str: str) -> str:
        """Generate Global Unicast IPv6 address from /64 prefix and MAC EUI-64."""
        net = ipaddress.IPv6Network(prefix_64.strip(), strict=False)
        if net.prefixlen != 64:
            raise ValueError(f"SLAAC requires a /64 prefix, got /{net.prefixlen}")
        
        prefix_exploded = net.network_address.exploded.split(":")[:4]
        eui64 = cls.mac_to_eui64(mac_str).split(":")
        
        full_hextets = prefix_exploded + eui64
        full_ip = ":".join(full_hextets)
        return cls.compress_ipv6(full_ip)
