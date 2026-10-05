# TRACK 10 // NETWORK AUTOMATION, PROGRAMMABILITY & NETDEVOPS

```
================================================================================
  SPECIFICATION: RFC 6241 (NETCONF) | RFC 8040 (RESTCONF) | RFC 7950 (YANG)
  THEME: Model-Driven Programmability, OpenConfig, Python Automation, GitOps
  COMPLIANCE: ZERO EMOJIS // NETDEVOPS SPECIFICATION
================================================================================
```

---

## 1. Model-Driven Programmability Stack

```
+-------------------------------------------------------------------------------+
| APPLICATION LAYER : Python (Netmiko, Scapy, Nornir), Ansible, Terraform       |
+-------------------------------------------------------------------------------+
| ENCODING LAYER    : JSON / XML (Strict Structured Serialization)              |
+-------------------------------------------------------------------------------+
| DATA MODEL LAYER  : YANG (IETF, OpenConfig, Native Vendor Models)             |
+-------------------------------------------------------------------------------+
| TRANSPORT PROTOCOL: NETCONF (SSH Port 830) | RESTCONF (HTTPS Port 443) | gNMI |
+-------------------------------------------------------------------------------+
| DEVICE CONTROL    : Linux Kernel / Network Operating System (ASIC Driver)     |
+-------------------------------------------------------------------------------+
```

### 1.1 NETCONF vs. RESTCONF Comparison

| Feature | NETCONF (RFC 6241) | RESTCONF (RFC 8040) |
| :--- | :--- | :--- |
| **Transport Protocol** | SSH (Port 830) / TLS | HTTPS (Port 443) |
| **Data Encoding** | XML | JSON or XML |
| **Operations** | `<get>`, `<get-config>`, `<edit-config>`, `<commit>` | GET, POST, PUT, PATCH, DELETE |
| **Datastores** | `running`, `startup`, `candidate` | Root resource mappings |
| **Transactionality** | Full multi-device atomic rollback & commit | Single-request atomic execution |

---

## 2. YANG Data Modeling (RFC 7950)

YANG is a declarative data modeling language used to define configuration and operational state data manipulated by NETCONF and RESTCONF.

```yang
module openconfig-interfaces {
  yang-version "1";
  namespace "http://openconfig.net/yang/interfaces";
  prefix "oc-if";

  container interfaces {
    list interface {
      key "name";
      leaf name {
        type string;
        description "The name of the interface (e.g., GigabitEthernet0/1)";
      }
      container config {
        leaf enabled {
          type boolean;
          default "true";
        }
        leaf description {
          type string;
        }
      }
    }
  }
}
```

---

## 3. Python NetDevOps Automation Directives

### 3.1 RESTCONF Interface Provisioning via Python

```python
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://192.168.1.1/restconf/data/openconfig-interfaces:interfaces/interface=GigabitEthernet0%2F1"
headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}
auth = HTTPBasicAuth("admin", "SecretPassword")

payload = {
    "openconfig-interfaces:interface": [
        {
            "name": "GigabitEthernet0/1",
            "config": {
                "name": "GigabitEthernet0/1",
                "type": "iana-if-type:ethernetCsmacd",
                "enabled": True,
                "description": "PROVISIONED_VIA_RESTCONF_PIPELINE"
            }
        }
    ]
}

response = requests.patch(url, auth=auth, headers=headers, json=payload, verify=False)
print(f"Status Code: {response.status_code}")
```

---

## 4. GitOps CI/CD Network Infrastructure Pipeline

```
[ Engineer Push ] 
       |
  (Git Repository: Pull Request)
       |
[ CI Validation Pipeline ]
  --> Syntax Linting (yamllint, flake8)
  --> Pre-flight Batfish Simulation (Verify no routing blackholes or ACL leaks)
  --> pyATS / Genie Unit Testing in Virtual Lab (Cisco CML / Containerlab)
       |
  (Merge to Main Branch)
       |
[ CD Deployment Pipeline ]
  --> Ansible / Nornir Push via NETCONF
  --> Automated Post-Deployment Verification (BGP adjacency count & ping checks)
  --> Auto-Rollback to Previous Git Commit if health tests fail
```
