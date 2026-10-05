# TRACK 08 // SERVICE PROVIDER ARCHITECTURE, MPLS, SEGMENT ROUTING & WAN

```
================================================================================
  SPECIFICATION: RFC 3031 (MPLS) | RFC 4364 (BGP/MPLS IP VPNs) | RFC 8402 (SR)
  THEME: Label Switching, L3VPN VRF Architecture, Segment Routing SRv6, SD-WAN
  COMPLIANCE: ZERO EMOJIS // SERVICE PROVIDER BLUEPRINT
================================================================================
```

---

## 1. Multiprotocol Label Switching (MPLS / RFC 3031)

MPLS replaces CPU-intensive IP routing table lookups with high-speed fixed 32-bit label swapping at the Provider (P) core.

```
+-------------------------------------------------------------------------------+
| 20 bits: Label Value (0 - 1,048,575)  | 3 bits: TC/Exp | 1 bit: S | 8 bits:TTL|
+-------------------------------------------------------------------------------+
```

- **Label Value (20 bits)**: Forwarding index in the LFIB (Label Forwarding Information Base).
  - Labels 0-15: Reserved (0: IPv4 Explicit NULL, 3: Implicit NULL [PHP], 7: Entropy).
- **Traffic Class / Experimental (TC/Exp, 3 bits)**: Quality of Service (QoS / DiffServ mapping).
- **Bottom of Stack (S, 1 bit)**: `1` indicates innermost label (last label before IP header); `0` indicates more labels follow.
- **Time to Live (TTL, 8 bits)**: Prevents label forwarding loops.

---

## 2. MPLS Layer 3 VPN Architecture (RFC 4364)

```
[ Customer A: Site 1 ]              [ Customer B: Site 1 ]
         |                                   |
    (CE Router)                         (CE Router)
         |                                   |
+--------v-----------------------------------v--------+
| [ PE-01 Router ]                      [ PE-02 Router ]
|  VRF Red (RD 65000:10, RT 65000:10)    VRF Red      |
|  VRF Blue(RD 65000:20, RT 65000:20)    VRF Blue     |
|          \                            /             |
|           [ P-01 Core ] --- [ P-02 ]                |
|           (MPLS Label Swapping Core)                |
+-----------------------------------------------------+
```

### 2.1 Core L3VPN Components

1. **VRF (Virtual Routing and Forwarding)**: Virtual routing tables on Provider Edge (PE) routers ensuring complete customer routing isolation.
2. **RD (Route Distinguisher, 64 bits)**: Prefixed to overlapping customer IPv4 addresses (e.g. `65000:10:192.168.1.0/24`) to create globally unique **VPN-IPv4** prefixes.
3. **RT (Route Target, 64-bit BGP Extended Community)**: Controls import and export policy of routes into customer VRF instances.
4. **Two-Label Forwarding Stack**:
   - **Outer Label (Transport / LDP)**: Swapped across P routers to reach egress PE.
   - **Inner Label (VPN / MP-BGP)**: Read by egress PE to identify target customer VRF.

---

## 3. Segment Routing (SR-MPLS & SRv6 / RFC 8402)

Segment Routing removes LDP and RSVP-TE signaling from the network core by encoding source-routed paths directly into the packet header (Source Routing paradigm).

```
+-------------------------------------------------------------------------------+
|                      SEGMENT ROUTING ARCHITECTURE MATRIX                      |
+-------------------------------------------------------------------------------+
| Feature       | SR-MPLS (Segment Routing MPLS)| SRv6 (Segment Routing IPv6)   |
+---------------+-------------------------------+-------------------------------+
| Data Plane    | Standard MPLS 32-bit Labels   | Native IPv6 Extension Headers |
| Header Field  | Segment List (Label Stack)    | Segment Routing Header (SRH)  |
| Underlay Req  | OSPF-SR / IS-IS-SR Extensions | Pure IPv6 Native Routing      |
| Network State | Zero state in P core routers  | Zero state in P core routers  |
+-------------------------------------------------------------------------------+
```

### 3.1 Segment Types (SIDs)
- **Node SID (Prefix SID)**: Identifies a specific router globally (advertised via IGP).
- **Adjacency SID (Adj-SID)**: Identifies a specific local egress link (strictly local).
- **Binding SID (BSID)**: Encapsulates complex TE policy into a single SID.
- **TI-LFA (Topology-Independent Loop-Free Alternate)**: Provides sub-50ms deterministic Fast Reroute (FRR) failover protection for any network topology.

---

## 4. Software-Defined WAN (SD-WAN Architecture)

```
[ Central Orchestrator / Controller: vManage / vSmart ]
                       |
     (Control Plane: OMP - Overlay Management Protocol)
                       |
+----------------------v----------------------------------+
|               SECURE OVERLAY IPSEC FABRIC                |
|                                                         |
|  [ Branch Edge Router ] ========= [ Hub / DC Router ]   |
|     | MPLS Link      \               /                  |
|     | Broadband ISP   \             /                   |
|     | 5G Wireless      \           /                    |
+---------------------------------------------------------+
```

### 4.1 Application-Aware Routing (AAR) Dynamic SLA Engine
SD-WAN edges continuously monitor jitter, packet loss, and latency using BFD (Bidirectional Forwarding Detection). Real-time traffic is steered automatically:
- **VoIP**: Requires Loss $< 1\%$, Latency $< 150\,\text{ms}$, Jitter $< 30\,\text{ms}$ $\to$ Steered to MPLS.
- **Bulk Cloud Traffic (Office365)** $\to$ Steered to Direct Internet Access (DIA).
