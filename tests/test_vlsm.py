"""Unit tests for VLSM Allocation, Supernet Aggregation & IPv6 Tools."""

import pytest
from src.subnetting.vlsm import VLSMPlanner
from src.subnetting.supernet import SupernetAggregator
from src.subnetting.ipv6_tools import IPv6Tools


def test_vlsm_allocation_standard():
    base = "192.168.1.0/24"
    requirements = [("Sales", 50), ("Engineering", 30), ("HR", 10), ("WAN", 2)]
    
    allocations = VLSMPlanner.allocate(base, requirements)
    assert len(allocations) == 4

    # Largest first: Sales (50 hosts -> /26, 62 usable)
    assert allocations[0].name == "Sales"
    assert allocations[0].cidr_prefix == 26
    assert allocations[0].network_address == "192.168.1.0"
    assert allocations[0].usable_hosts == 62

    # Engineering (30 hosts -> /27, 30 usable)
    assert allocations[1].name == "Engineering"
    assert allocations[1].cidr_prefix == 27
    assert allocations[1].network_address == "192.168.1.64"

    # HR (10 hosts -> /28, 14 usable)
    assert allocations[2].name == "HR"
    assert allocations[2].cidr_prefix == 28
    assert allocations[2].network_address == "192.168.1.96"

    # WAN (2 hosts -> /30, 2 usable)
    assert allocations[3].name == "WAN"
    assert allocations[3].cidr_prefix == 30
    assert allocations[3].network_address == "192.168.1.112"


def test_vlsm_insufficient_space():
    base = "192.168.1.0/28"  # Only 16 addresses
    requirements = [("BigDept", 100)]
    with pytest.raises(ValueError):
        VLSMPlanner.allocate(base, requirements)


def test_supernet_aggregation():
    nets = ["192.168.0.0/24", "192.168.1.0/24", "192.168.2.0/24", "192.168.3.0/24"]
    supernet = SupernetAggregator.summarize(nets)
    assert supernet == "192.168.0.0/22"

    nets_single = ["10.1.0.0/16"]
    assert SupernetAggregator.summarize(nets_single) == "10.1.0.0/16"


def test_ipv6_tools():
    # EUI-64 generation: 00:1A:2B:3C:4D:5E -> 021a:2bff:fe3c:4d5e
    eui64 = IPv6Tools.mac_to_eui64("00:1A:2B:3C:4D:5E")
    assert eui64 == "021a:2bff:fe3c:4d5e"

    # Link-Local SLAAC
    slaac = IPv6Tools.generate_slaac_link_local("00:1A:2B:3C:4D:5E")
    assert slaac == "fe80::21a:2bff:fe3c:4d5e"

    # Global SLAAC
    global_slaac = IPv6Tools.generate_slaac_global("2001:db8:acad:1::/64", "00:1A:2B:3C:4D:5E")
    assert global_slaac == "2001:db8:acad:1:21a:2bff:fe3c:4d5e"
