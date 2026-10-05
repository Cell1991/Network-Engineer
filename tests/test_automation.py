"""Unit tests for Automation, Config Diff, Templates, and CLI functions."""

import subprocess
import sys
import pytest
from src.automation.config_differ import NetworkConfigDiffer
from src.automation.template_engine import NetworkTemplateEngine, InterfaceConfig, BGPConfig
from src.automation.yang_parser import RESTCONFSerializer


def test_config_differ():
    base_cfg = """
interface GigabitEthernet0/0/0
 description UPLINK-TO-ISP1
 ip address 203.0.113.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/0/1
 description OLD-LEGACY-LINK
 shutdown
!
"""
    target_cfg = """
interface GigabitEthernet0/0/0
 description UPLINK-TO-ISP1-PRIMARY
 ip address 203.0.113.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/0/2
 description NEW-LAN-CORE
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
"""
    delta = NetworkConfigDiffer.diff(base_cfg, target_cfg)
    assert "interface GigabitEthernet0/0/2" in delta.added_sections
    assert "interface GigabitEthernet0/0/1" in delta.removed_sections
    assert "interface GigabitEthernet0/0/0" in delta.modified_sections


def test_template_rendering():
    ifaces = [
        InterfaceConfig(name="GigabitEthernet0/1", description="SERVER-ACCESS", ipv4_address="192.168.10.1/24", vlan_id=10)
    ]
    bgp = BGPConfig(
        local_as=65000,
        router_id="10.255.255.1",
        neighbors=[{"ip": "10.0.0.2", "remote_as": 65001, "description": "PEER-AS65001"}],
        networks=["192.168.10.0/24"]
    )

    cisco_out = NetworkTemplateEngine.render_cisco_ios(ifaces, bgp)
    assert "interface GigabitEthernet0/1" in cisco_out
    assert "router bgp 65000" in cisco_out
    assert "neighbor 10.0.0.2 remote-as 65001" in cisco_out

    junos_out = NetworkTemplateEngine.render_junos(ifaces, bgp)
    assert "interfaces {" in junos_out
    assert "GigabitEthernet0/1 {" in junos_out


def test_yang_restconf_serialization():
    ifaces = [{"name": "eth0", "enabled": True, "description": "UPLINK", "ipv4_address": "192.168.1.1/24"}]
    res = RESTCONFSerializer.serialize_openconfig_interfaces(ifaces)
    assert "openconfig-interfaces:interfaces" in res
    assert "eth0" in res


def test_cli_execution():
    # Test CLI subnet execution
    res = subprocess.run([sys.executable, "-m", "src.cli", "subnet", "192.168.1.1/24"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "192.168.1.0" in res.stdout

    # Test CLI STP execution
    res_stp = subprocess.run([sys.executable, "-m", "src.cli", "stp-sim"], capture_output=True, text=True)
    assert res_stp.returncode == 0
    assert "ELECTED ROOT BRIDGE" in res_stp.stdout
