# TRACK 12 // CLOUD NETWORKING & HYBRID INTERCONNECT ARCHITECTURES

```
================================================================================
  SPECIFICATION: AWS Direct Connect / VPC | Azure ExpressRoute / VNet | GCP VPC
  THEME: Transit Gateway, Multi-Cloud Overlays, Cloud Interconnects & Peering
  COMPLIANCE: ZERO EMOJIS // CLOUD NETWORKING BLUEPRINT
================================================================================
```

---

## 1. Cloud Virtual Private Cloud (VPC) Underpinnings

Cloud VPCs are Software-Defined Network (SDN) overlay networks constructed on hypervisor-level Geneve / VXLAN encapsulations.

```
+-------------------------------------------------------------------------------+
|                      MULTI-CLOUD CONCEPTS MAPPING MATRIX                      |
+-------------------------------------------------------------------------------+
| Architecture Concept      | AWS                      | Azure                  |
+---------------------------+--------------------------+------------------------+
| Isolated Network Domain   | VPC (Virtual Priv Cloud) | VNet (Virtual Network) |
| Dedicated Physical WAN    | AWS Direct Connect (DX)  | Azure ExpressRoute     |
| Multi-VPC Transit Hub     | AWS Transit Gateway(TGW) | Azure Virtual WAN Hub  |
| L4/L7 Ingress Load Balancer| NLB (Network LB) / ALB  | Azure Load Balancer    |
| Ingress / Egress Gateway  | Internet Gateway (IGW)   | Azure NAT Gateway      |
+-------------------------------------------------------------------------------+
```

---

## 2. Dedicated Cloud Interconnect (AWS Direct Connect / Azure ExpressRoute)

```
[ On-Premises Enterprise Core ]
               |
         (802.1Q Trunk / LACP)
               |
[ Colocation Meet-Me Room (Equinix / CoreSite) ]
               |
       (Direct Fiber Cross-Connect: 10G / 100G)
               |
+--------------v------------------------------------------------+
| AWS Direct Connect Location / Cloud Router                    |
|   - Private VIF (Virtual Interface) -> BGP Peering (AS 64512) |
|   - Transit VIF -> Direct Connect Gateway -> AWS TGW Hub      |
+---------------------------------------------------------------+
```

### 2.1 BGP Peering over Direct Connect / ExpressRoute
- **BGP ASN**: On-premise private ASN (e.g. `65000`) peers with Cloud Router ASN (`64512` or Microsoft ASN `12076`).
- **BFD (Bidirectional Forwarding Detection)**: Sub-second link failure detection (e.g., $3 \times 300\,\text{ms} = 900\,\text{ms}$ failover).
- **Redundancy**: Dual Active/Active physical cross-connects terminate on diverse colocation chassis for 99.99% availability SLAs.

---

## 3. Hub-and-Spoke Multi-VPC Transit Gateway (TGW)

```
       [ AWS TRANSIT GATEWAY (TGW): Central Routing Hub ]
         /           |                  \              \
        /            |                   \              \
 [ VPC 1: Prod ]  [ VPC 2: Dev ]    [ VPC 3: DMZ ]   [ AWS Direct Connect ]
 (10.100.0.0/16)  (10.101.0.0/16)   (10.200.0.0/16)  (On-Premises Data Ctr)
```

- **TGW Route Tables**: Enables network segmentation (e.g., Prod VPC isolated from Dev VPC, while both route through DMZ Inspection VPC for firewall filtering).
- **East-West Traffic Inspection**: Intercepts traffic between VPCs using Gateway Load Balancers (GWLB) and GENEVE tunneling to NGFW appliances.
