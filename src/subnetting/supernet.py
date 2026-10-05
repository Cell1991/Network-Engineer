"""
CIDR Route Aggregation / Supernetting Engine.
Computes minimal summarizing supernet prefixes for multiple subnets.
"""

from typing import List
from .calculator import IPv4Calculator


class SupernetAggregator:
    """Computes exact and minimal covering supernets for routing table optimization."""

    @classmethod
    def summarize(cls, networks: List[str]) -> str:
        """
        Summarize a collection of IPv4 CIDR blocks into their minimal covering supernet.
        Example: ['192.168.0.0/24', '192.168.1.0/24', '192.168.2.0/24', '192.168.3.0/24']
        -> '192.168.0.0/22'
        """
        if not networks:
            raise ValueError("Network list cannot be empty")

        min_ip_int = 0xFFFFFFFF
        max_ip_int = 0x00000000

        for net in networks:
            info = IPv4Calculator.calculate(net)
            net_start = IPv4Calculator.ip_to_int(info.network_address)
            net_end = IPv4Calculator.ip_to_int(info.broadcast_address)

            if net_start < min_ip_int:
                min_ip_int = net_start
            if net_end > max_ip_int:
                max_ip_int = net_end

        # Find the number of common leading bits between min_ip_int and max_ip_int
        diff = min_ip_int ^ max_ip_int
        common_bits = 32 - diff.bit_length()

        # The supernet mask is common_bits
        supernet_prefix = max(0, common_bits)
        mask = IPv4Calculator.prefix_to_mask_int(supernet_prefix)
        supernet_base_int = min_ip_int & mask

        return f"{IPv4Calculator.int_to_ip(supernet_base_int)}/{supernet_prefix}"
