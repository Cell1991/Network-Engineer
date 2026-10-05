"""
IPv4 Address & Subnet Calculation Engine.
Performs RFC 791 / RFC 4632 compliant bitwise address arithmetic,
wildcard mask calculations, usable host boundaries, and classful/RFC1918 classification.
"""

from dataclasses import dataclass
import struct
import socket
from typing import Tuple, List, Optional


@dataclass(frozen=True)
class SubnetInfo:
    ip_address: str
    cidr_prefix: int
    netmask: str
    wildcard_mask: str
    network_address: str
    broadcast_address: str
    first_usable_ip: str
    last_usable_ip: str
    total_hosts: int
    usable_hosts: int
    ip_binary: str
    netmask_binary: str
    ip_class: str
    is_private_rfc1918: bool
    is_loopback: bool
    is_multicast: bool
    is_link_local: bool


class IPv4Calculator:
    """Rigorous bitwise IPv4 subnetting and address inspection calculator."""

    @staticmethod
    def ip_to_int(ip_str: str) -> int:
        """Convert dotted-decimal IPv4 string to 32-bit unsigned integer."""
        octets = ip_str.strip().split(".")
        if len(octets) != 4:
            raise ValueError(f"Invalid IPv4 string: '{ip_str}' must have 4 octets")
        val = 0
        for octet in octets:
            if not octet.isdigit():
                raise ValueError(f"Invalid octet: '{octet}' is not an integer")
            num = int(octet)
            if num < 0 or num > 255:
                raise ValueError(f"Octet value out of range [0-255]: {num}")
            val = (val << 8) | num
        return val

    @staticmethod
    def int_to_ip(ip_int: int) -> str:
        """Convert 32-bit unsigned integer to dotted-decimal IPv4 string."""
        if ip_int < 0 or ip_int > 0xFFFFFFFF:
            raise ValueError(f"Integer out of 32-bit IPv4 range: {ip_int}")
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"

    @staticmethod
    def int_to_binary_str(ip_int: int) -> str:
        """Convert 32-bit integer into dotted-binary string representation."""
        octets = [
            f"{(ip_int >> 24) & 0xFF:08b}",
            f"{(ip_int >> 16) & 0xFF:08b}",
            f"{(ip_int >> 8) & 0xFF:08b}",
            f"{ip_int & 0xFF:08b}",
        ]
        return ".".join(octets)

    @classmethod
    def prefix_to_mask_int(cls, prefix: int) -> int:
        """Convert CIDR prefix length (0-32) to 32-bit integer netmask."""
        if prefix < 0 or prefix > 32:
            raise ValueError(f"CIDR prefix must be between 0 and 32, got: {prefix}")
        if prefix == 0:
            return 0
        return ((1 << prefix) - 1) << (32 - prefix)

    @classmethod
    def mask_str_to_prefix(cls, mask_str: str) -> int:
        """Convert dotted-decimal netmask string to CIDR prefix length."""
        mask_int = cls.ip_to_int(mask_str)
        # Verify contiguous 1s from MSB
        seen_zero = False
        prefix = 0
        for i in range(31, -1, -1):
            bit = (mask_int >> i) & 1
            if bit == 1:
                if seen_zero:
                    raise ValueError(f"Non-contiguous netmask: '{mask_str}'")
                prefix += 1
            else:
                seen_zero = True
        return prefix

    @classmethod
    def classify_classful(cls, ip_int: int) -> str:
        """Return legacy classful categorization (Class A, B, C, D, E)."""
        first_octet = (ip_int >> 24) & 0xFF
        if first_octet < 128:
            return "Class A"
        elif first_octet < 192:
            return "Class B"
        elif first_octet < 224:
            return "Class C"
        elif first_octet < 240:
            return "Class D (Multicast)"
        else:
            return "Class E (Experimental)"

    @classmethod
    def is_private_rfc1918(cls, ip_int: int) -> bool:
        """Check if IP falls within RFC 1918 private address ranges."""
        # 10.0.0.0/8 (10.0.0.0 - 10.255.255.255)
        # 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
        # 192.168.0.0/16 (192.168.0.0 - 192.168.255.255)
        o1 = (ip_int >> 24) & 0xFF
        o2 = (ip_int >> 16) & 0xFF
        if o1 == 10:
            return True
        if o1 == 172 and 16 <= o2 <= 31:
            return True
        if o1 == 192 and o2 == 168:
            return True
        return False

    @classmethod
    def calculate(cls, ip_str_with_cidr: str) -> SubnetInfo:
        """
        Calculate complete subnet metrics for given IP/CIDR or IP/Mask.
        Example: '192.168.1.50/24' or '10.20.30.40/255.255.240.0'
        """
        raw = ip_str_with_cidr.strip()
        if "/" in raw:
            parts = raw.split("/")
            ip_str = parts[0].strip()
            mask_part = parts[1].strip()
            if "." in mask_part:
                cidr = cls.mask_str_to_prefix(mask_part)
            else:
                cidr = int(mask_part)
        else:
            ip_str = raw
            cidr = 32

        if cidr < 0 or cidr > 32:
            raise ValueError(f"CIDR prefix must be between 0 and 32, got {cidr}")

        ip_int = cls.ip_to_int(ip_str)
        mask_int = cls.prefix_to_mask_int(cidr)
        wildcard_int = (~mask_int) & 0xFFFFFFFF
        network_int = ip_int & mask_int
        broadcast_int = network_int | wildcard_int

        total_hosts = 1 << (32 - cidr)
        if cidr == 32:
            usable_hosts = 1
            first_usable_int = ip_int
            last_usable_int = ip_int
        elif cidr == 31:
            # RFC 3021 Point-to-Point Links
            usable_hosts = 2
            first_usable_int = network_int
            last_usable_int = broadcast_int
        else:
            usable_hosts = max(0, total_hosts - 2)
            first_usable_int = network_int + 1
            last_usable_int = broadcast_int - 1

        o1 = (ip_int >> 24) & 0xFF
        o2 = (ip_int >> 16) & 0xFF
        is_loopback = (o1 == 127)
        is_multicast = (224 <= o1 <= 239)
        is_link_local = (o1 == 169 and o2 == 254)

        return SubnetInfo(
            ip_address=cls.int_to_ip(ip_int),
            cidr_prefix=cidr,
            netmask=cls.int_to_ip(mask_int),
            wildcard_mask=cls.int_to_ip(wildcard_int),
            network_address=cls.int_to_ip(network_int),
            broadcast_address=cls.int_to_ip(broadcast_int),
            first_usable_ip=cls.int_to_ip(first_usable_int),
            last_usable_ip=cls.int_to_ip(last_usable_int),
            total_hosts=total_hosts,
            usable_hosts=usable_hosts,
            ip_binary=cls.int_to_binary_str(ip_int),
            netmask_binary=cls.int_to_binary_str(mask_int),
            ip_class=cls.classify_classful(ip_int),
            is_private_rfc1918=cls.is_private_rfc1918(ip_int),
            is_loopback=is_loopback,
            is_multicast=is_multicast,
            is_link_local=is_link_local,
        )
