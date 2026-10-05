"""
YANG Schema (RFC 6020 / RFC 7950) & RESTCONF Serializer.
Encodes network state into OpenConfig / IETF YANG structured JSON payloads.
"""

from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional


@dataclass
class SimpleYANGModel:
    module_name: str
    namespace: str
    prefix: str


class RESTCONFSerializer:
    """Serializes network interfaces and routing entities to RFC 8040 RESTCONF JSON."""

    @staticmethod
    def serialize_openconfig_interfaces(interfaces: List[dict]) -> str:
        """
        Serialize interface list to OpenConfig `openconfig-interfaces:interfaces` YANG model.
        """
        oc_ifaces = []
        for iface in interfaces:
            entry = {
                "name": iface["name"],
                "config": {
                    "name": iface["name"],
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": iface.get("enabled", True),
                    "description": iface.get("description", "")
                },
                "state": {
                    "admin-status": "UP" if iface.get("enabled", True) else "DOWN",
                    "oper-status": "UP" if iface.get("enabled", True) else "DOWN",
                    "counters": {
                        "in-octets": iface.get("in_octets", 0),
                        "out-octets": iface.get("out_octets", 0),
                        "in-errors": 0,
                        "out-errors": 0
                    }
                }
            }

            if "ipv4_address" in iface and iface["ipv4_address"]:
                ip, pfx = iface["ipv4_address"].split("/")
                entry["subinterfaces"] = {
                    "subinterface": [
                        {
                            "index": 0,
                            "openconfig-if-ip:ipv4": {
                                "addresses": {
                                    "address": [
                                        {
                                            "ip": ip,
                                            "config": {
                                                "ip": ip,
                                                "prefix-length": int(pfx)
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }

            oc_ifaces.append(entry)

        payload = {
            "openconfig-interfaces:interfaces": {
                "interface": oc_ifaces
            }
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def serialize_ietf_bgp(local_as: int, router_id: str, neighbors: List[dict]) -> str:
        """Serialize BGP configuration into IETF BGP YANG model (RFC 8040)."""
        payload = {
            "ietf-bgp:bgp": {
                "global": {
                    "as": local_as,
                    "router-id": router_id
                },
                "neighbors": {
                    "neighbor": [
                        {
                            "neighbor-address": nbr["ip"],
                            "config": {
                                "peer-as": nbr["remote_as"],
                                "description": nbr.get("description", "")
                            }
                        }
                        for nbr in neighbors
                    ]
                }
            }
        }
        return json.dumps(payload, indent=2)
