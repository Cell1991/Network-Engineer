# TRACK 04 // UNICAST & MULTICAST ROUTING ARCHITECTURES

```
================================================================================
  SPECIFICATION: RFC 2328 (OSPFv2) | RFC 5340 (OSPFv3) | RFC 4271 (BGP-4) | IS-IS
  THEME: Link-State SPF, Path-Vector BGP, MP-BGP EVPN, LFA FRR, Multicast PIM
  COMPLIANCE: ZERO EMOJIS // HIGH-TECH PROTOCOL COMPENDIUM
================================================================================
```

---

## 1. Routing Taxonomy & Administrative Distance

```
+-------------------------------------------------------------------------------+
|                       ROUTING PROTOCOL TAXONOMY MATRIX                        |
+-------------------------------------------------------------------------------+
| Protocol  | Protocol Class | Metric Formula                 | Admin Distance  |
+-----------+----------------+--------------------------------+-----------------+
| Connected | Direct L1/L2   | 0                              | 0               |
| Static    | Deterministic  | Hop / Metric                   | 1               |
| eBGP      | Path-Vector    | Path Attributes                | 20              |
| EIGRP     | Advanced DV    | Bandwidth + Delay composite    | 90 (Int)/170(Ext|
| OSPF      | Link-State     | Cost = Ref_BW / Interface_BW   | 110             |
| IS-IS     | Link-State     | Configured Interface Cost (10) | 115             |
| RIPv2     | Distance-Vector| Hop Count (1-15, 16=Inf)       | 120             |
| iBGP      | Path-Vector    | Path Attributes                | 200             |
+-------------------------------------------------------------------------------+
```

---

## 2. OSPFv2 & OSPFv3 (Open Shortest Path First)

OSPF is a link-state routing protocol based on Dijkstra's Shortest Path First algorithm. Every router in an OSPF Area maintains an identical Link-State Database (LSDB).

```
               [ AREA 0: BACKBONE CORE ]
              /                         \
       (ABR Router 1)             (ABR Router 2)
            /                                 \
  [ AREA 1: CAMPUS LAN ]            [ AREA 2: DATA CENTER ]
     - Type 1, 2 LSAs                  - Type 1, 2 LSAs
     - Type 3 Summary LSAs             - Type 3 Summary LSAs
```

### 2.1 Standard OSPF LSA Types

| LSA Type | Name | Originator | Flooding Scope | Contents |
| :--- | :--- | :--- | :--- | :--- |
| **Type 1** | Router LSA | Every router | Intra-area | Advertises router interfaces, links, and IP prefixes |
| **Type 2** | Network LSA | Designated Router (DR) | Intra-area | Multi-access broadcast network router membership list |
| **Type 3** | Summary LSA | Area Border Router (ABR) | Inter-area | Inter-area prefix summaries injected into other areas |
| **Type 4** | ASBR Summary | ABR | Inter-area | Host route to ASBR (Autonomous System Boundary Router) |
| **Type 5** | AS-External | ASBR | Entire OSPF Domain | External routes redistributed into OSPF (E1/E2) |
| **Type 7** | NSSA External | ASBR in NSSA Area | NSSA Area only | External routes converted to Type 5 by ABR |

### 2.2 OSPF Neighbor State Machine

```
[ DOWN ] --> [ ATTEMPT ] --> [ INIT ] --> [ 2-WAY ] 
                                             |  (DR/BDR Election on Broadcast links)
[ FULL ] <-- [ LOADING ] <-- [ EXCHANGE ] <-- [ EXSTART ]
```

1. **Down**: No Hello packets received.
2. **Init**: Received Hello from neighbor; local Router ID not yet listed in neighbor's seen list.
3. **2-Way**: Bidirectional communication confirmed (Router ID seen in neighbor Hello). DR/BDR elected.
4. **ExStart**: Master/Slave negotiation and Initial Sequence Number (ISN) agreement for DBD exchange.
5. **Exchange**: Routers exchange Database Description (DBD) packets summarizing LSDB contents.
6. **Loading**: Routers send Link State Requests (LSR) for missing LSAs; receive Link State Updates (LSU).
7. **Full**: LSDBs are 100% synchronized. Dijkstra SPF executes to generate routing table.

---

## 3. Border Gateway Protocol (BGP-4 / RFC 4271)

BGP-4 is the exterior gateway routing protocol that interconnects Autonomous Systems (AS) across the global Internet.

```
       [ AS 65001: ENTERPRISE HQ ]
              |          \
        (eBGP Peering)   (eBGP Peering)
              |            \
       [ AS 174: COGENT ]  [ AS 3356: LUMEN ]
              \            /
          [ GLOBAL INTERNET ]
```

### 3.1 BGP-4 Best Path Selection Algorithm (Deterministic 10-Step Order)

```
Candidate Paths for Prefix X
  |
  +--> [1. Highest WEIGHT] (Cisco Local: 0-65535, Default: 32768/0)
  |      |
  +--> [2. Highest LOCAL_PREF] (Propagated in iBGP, Default: 100)
  |      |
  +--> [3. Prefer LOCALLY ORIGINATED] (network/aggregate > redistribute)
  |      |
  +--> [4. Shortest AS_PATH] (Counts AS hops; AS_SET=1, AS_CONFED ignored)
  |      |
  +--> [5. Lowest ORIGIN Code] (IGP 'i' < EGP 'e' < Incomplete '?')
  |      |
  +--> [6. Lowest MED] (Multi-Exit Discriminator; compared within same neighbor AS)
  |      |
  +--> [7. Prefer eBGP over iBGP] (External peers preferred)
  |      |
  +--> [8. Lowest IGP Metric to BGP Next-Hop] (Hot-potato routing)
  |      |
  +--> [9. Oldest eBGP Route] (Stability tiebreaker against route flaps)
  |      |
  +--> [10. Lowest BGP Router ID (RID)] (Final tiebreaker, then lowest peer IP)
```

---

## 4. Multicast Routing (PIM-SM & IGMP)

```
[ Video Multicast Source: 239.1.1.100 ]
               |
        [ First-Hop Router (FHR) ]
               |
         (PIM Sparse-Mode (*,G) and (S,G) Trees)
               |
        [ Rendezvous Point (RP) ]
               |
        [ Last-Hop Router (LHR) ]
               |
         (IGMPv3 Membership Report)
               |
[ Receiver Host ]
```

- **IGMP (Internet Group Management Protocol)**: Host-to-router protocol for joining multicast groups.
  - IGMPv1: Basic membership query/report.
  - IGMPv2: Adds explicit Leave Group message (Group-Specific Query) to reduce leave latency.
  - IGMPv3: Adds Source-Specific Multicast (SSM: `INCLUDE`/`EXCLUDE` source IP filters).
- **PIM-SM (Protocol Independent Multicast - Sparse Mode)**:
  - Shared Tree ($*, G$): Rooted at the **Rendezvous Point (RP)**.
  - Shortest Path Tree ($S, G$): Built directly from receiver to source once threshold bandwidth is exceeded (SPT Switchover).
