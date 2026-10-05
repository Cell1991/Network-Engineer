"""Unit tests for IPv4 Subnetting, bitwise arithmetic, and classification."""

import pytest
from src.subnetting.calculator import IPv4Calculator


def test_ip_to_int_and_back():
    ip = "192.168.1.1"
    ip_int = IPv4Calculator.ip_to_int(ip)
    assert ip_int == 0xC0A80101
    assert IPv4Calculator.int_to_ip(ip_int) == ip


def test_invalid_ip_raises():
    with pytest.raises(ValueError):
        IPv4Calculator.ip_to_int("256.0.0.1")
    with pytest.raises(ValueError):
        IPv4Calculator.ip_to_int("192.168.1")
    with pytest.raises(ValueError):
        IPv4Calculator.ip_to_int("abc.def.ghi.jkl")


def test_prefix_to_mask_and_back():
    assert IPv4Calculator.prefix_to_mask_int(24) == 0xFFFFFF00
    assert IPv4Calculator.mask_str_to_prefix("255.255.255.0") == 24
    assert IPv4Calculator.mask_str_to_prefix("255.255.240.0") == 20
    assert IPv4Calculator.mask_str_to_prefix("255.0.0.0") == 8
    assert IPv4Calculator.mask_str_to_prefix("0.0.0.0") == 0


def test_subnet_info_slash_24():
    info = IPv4Calculator.calculate("192.168.10.45/24")
    assert info.network_address == "192.168.10.0"
    assert info.broadcast_address == "192.168.10.255"
    assert info.netmask == "255.255.255.0"
    assert info.wildcard_mask == "0.0.0.255"
    assert info.first_usable_ip == "192.168.10.1"
    assert info.last_usable_ip == "192.168.10.254"
    assert info.total_hosts == 256
    assert info.usable_hosts == 254
    assert info.is_private_rfc1918 is True
    assert info.ip_class == "Class C"


def test_subnet_info_slash_30_and_31():
    # /30 Point-to-Point
    info30 = IPv4Calculator.calculate("10.0.0.1/30")
    assert info30.total_hosts == 4
    assert info30.usable_hosts == 2
    assert info30.network_address == "10.0.0.0"
    assert info30.broadcast_address == "10.0.0.3"
    assert info30.first_usable_ip == "10.0.0.1"
    assert info30.last_usable_ip == "10.0.0.2"

    # /31 RFC 3021
    info31 = IPv4Calculator.calculate("10.0.0.0/31")
    assert info31.usable_hosts == 2
    assert info31.first_usable_ip == "10.0.0.0"
    assert info31.last_usable_ip == "10.0.0.1"


def test_rfc1918_classification():
    assert IPv4Calculator.is_private_rfc1918(IPv4Calculator.ip_to_int("10.50.1.1")) is True
    assert IPv4Calculator.is_private_rfc1918(IPv4Calculator.ip_to_int("172.20.10.5")) is True
    assert IPv4Calculator.is_private_rfc1918(IPv4Calculator.ip_to_int("172.35.0.1")) is False
    assert IPv4Calculator.is_private_rfc1918(IPv4Calculator.ip_to_int("192.168.100.1")) is True
    assert IPv4Calculator.is_private_rfc1918(IPv4Calculator.ip_to_int("8.8.8.8")) is False
