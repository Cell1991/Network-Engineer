"""
Variable Length Subnet Mask (VLSM) Optimal Allocator.
Calculates non-overlapping hierarchical subnet partitioning based on host requirements,
minimizing address space fragmentation.
"""

from dataclasses import dataclass
import math
from typing import List, Tuple
from .calculator import IPv4Calculator, SubnetInfo


@dataclass(frozen=True)
class SubnetAllocation:
    name: str
    required_hosts: int
    allocated_hosts: int
    usable_hosts: int
    cidr_prefix: int
    netmask: str
    network_address: str
    broadcast_address: str
    first_usable_ip: str
    last_usable_ip: str


class VLSMPlanner:
    """Computes mathematically optimal VLSM partitions."""

    @classmethod
    def calculate_required_prefix(cls, hosts_needed: int) -> int:
        """
        Determine minimum CIDR prefix that can accommodate `hosts_needed` hosts.
        Formula: 2^(32 - prefix) - 2 >= hosts_needed (for prefix <= 30).
        For hosts_needed == 2: /30 gives 2 usable hosts (or /31 for RFC3021).
        """
        if hosts_needed <= 0:
            raise ValueError(f"Host requirement must be positive, got: {hosts_needed}")
        
        # We need total addresses = hosts_needed + 2 (network + broadcast)
        total_needed = hosts_needed + 2
        # Smallest power of 2 >= total_needed
        host_bits = math.ceil(math.log2(total_needed))
        if host_bits < 2:
            host_bits = 2  # /30 minimum for standard broadcast domains
        prefix = 32 - host_bits
        if prefix < 0:
            raise ValueError(f"Host count {hosts_needed} exceeds entire 32-bit IPv4 space")
        return prefix

    @classmethod
    def allocate(
        cls,
        base_network: str,
        requirements: List[Tuple[str, int]]
    ) -> List[SubnetAllocation]:
        """
        Allocate contiguous subnets from `base_network` (e.g. '192.168.1.0/24')
        for list of (name, host_count) tuples.
        Algorithm: Sort requirements in DESCENDING order of size to eliminate fragmentation.
        """
        base_info = IPv4Calculator.calculate(base_network)
        base_net_int = IPv4Calculator.ip_to_int(base_info.network_address)
        base_total_hosts = base_info.total_hosts

        # Sort requirements descending by host count
        sorted_reqs = sorted(requirements, key=lambda x: x[1], reverse=True)

        current_ip_int = base_net_int
        allocations: List[SubnetAllocation] = []

        for name, needed in sorted_reqs:
            prefix = cls.calculate_required_prefix(needed)
            block_size = 1 << (32 - prefix)

            # Check if this allocation fits within base network bounds
            if (current_ip_int + block_size) > (base_net_int + base_total_hosts):
                raise ValueError(
                    f"Insufficient address space: cannot allocate '{name}' ({needed} hosts) "
                    f"in base block {base_network}"
                )

            sub_info = IPv4Calculator.calculate(f"{IPv4Calculator.int_to_ip(current_ip_int)}/{prefix}")
            
            allocations.append(
                SubnetAllocation(
                    name=name,
                    required_hosts=needed,
                    allocated_hosts=sub_info.total_hosts,
                    usable_hosts=sub_info.usable_hosts,
                    cidr_prefix=prefix,
                    netmask=sub_info.netmask,
                    network_address=sub_info.network_address,
                    broadcast_address=sub_info.broadcast_address,
                    first_usable_ip=sub_info.first_usable_ip,
                    last_usable_ip=sub_info.last_usable_ip,
                )
            )

            current_ip_int += block_size

        return allocations
