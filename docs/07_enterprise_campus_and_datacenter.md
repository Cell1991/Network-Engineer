# TRACK 07 // ENTERPRISE CAMPUS DESIGN, DATA CENTER NETWORKS & WIRELESS

```
================================================================================
  SPECIFICATION: Cisco 3-Tier Enterprise | Clos 2-Tier Spine-Leaf | IEEE 802.11be
  THEME: Core/Distribution/Access, Spine-Leaf Fabrics, Wi-Fi 6/7, FHRP, EVPN-MH
  COMPLIANCE: ZERO EMOJIS // SYSTEM ARCHITECTURE SPECIFICATION
================================================================================
```

---

## 1. Enterprise Campus 3-Tier Hierarchical Architecture

```
                  [ 1. CORE LAYER ]
              (High-Speed L3 Packet Forwarding)
                  /                      \
      [ CORE SWITCH 01 ] ============ [ CORE SWITCH 02 ]
             /        \              /        \
            /          \            /          \
  [ DIST SWITCH 01 ] === [ DIST SWITCH 02 ]   [ DIST SWITCH 03 ] === [ DIST SWITCH 04 ]
           \                 /                       \                 /
            \               /                         \               /
       [ 2. DISTRIBUTION LAYER: Policy Boundaries, Inter-VLAN Routing, ACLs, QoS ]
            /               \                         /               \
   [ ACC SW 01 ]      [ ACC SW 02 ]             [ ACC SW 03 ]      [ ACC SW 04 ]
            |                  |                         |                  |
       [ 3. ACCESS LAYER: 802.1X Port Security, PoE+ (802.3bt), Endpoints, Wi-Fi APs ]
```

### 1.1 First Hop Redundancy Protocols (FHRP)

```
+-------------------------------------------------------------------------------+
|                      FHRP PROTOCOL COMPARISON MATRIX                          |
+-------------------------------------------------------------------------------+
| Protocol | Standard  | Virtual MAC Address     | Active/Standby Logic         |
+----------+-----------+-------------------------+------------------------------+
| HSRPv1   | Cisco     | 0000.0c07.acXX (XX=Grp) | 1 Active, 1 Standby          |
| HSRPv2   | Cisco     | 0000.0c9f.fXXX (XXX=Grp)| 1 Active, 1 Standby          |
| VRRPv2/3 | IETF Open | 0000.5e00.01XX (XX=VRID)| 1 Master, N Backups          |
| GLBP     | Cisco     | 0007.b400.XXYY          | Active Load Balancing (AVG)  |
+-------------------------------------------------------------------------------+
```

---

## 2. Modern Data Center 2-Tier Clos (Spine-Leaf) Fabric

Modern hyper-scale data centers reject spanning-tree loops in favor of Layer 3 ECMP (Equal-Cost Multi-Path) non-blocking Clos networks.

```
       [ SPINE-01 ]          [ SPINE-02 ]          [ SPINE-03 ]          [ SPINE-04 ]
         / | \ \                / | \ \                / | \ \                / | \ \
        /  |  \  \             /  |  \  \             /  |  \  \             /  |  \  \
       /   |   \   \          /   |   \   \          /   |   \   \          /   |   \   \
  [ LEAF-01 ]   [ LEAF-02 ]   [ LEAF-03 ]   [ LEAF-04 ]   [ LEAF-05 ]   [ LEAF-06 ]
     (ToR)         (ToR)         (ToR)         (ToR)         (ToR)         (ToR)
       |             |             |             |             |             |
  [ COMPUTE ]   [ STORAGE ]   [ K8s NODE]   [ DB CLUSTER] [ BARE-METAL] [ GPU RACK ]
```

### 2.1 Spine-Leaf Design Rules
1. **Zero Spine-to-Spine links**: Spines do not connect to each other.
2. **Zero Leaf-to-Leaf links**: Leaves do not connect directly to each other (unless running MC-LAG / vPC pair).
3. **Full Mesh**: Every Leaf connects to EVERY Spine.
4. **Predictable Latency Guarantee**: Any server can reach any other server in exactly 2 hops (Leaf $\to$ Spine $\to$ Leaf).

---

## 3. Wireless LAN Architecture (Wi-Fi 6 / 6E / 7 & CAPWAP)

```
[ Centralized Wireless LAN Controller (WLC) ]
                 |
   (CAPWAP Control & Data UDP Tunnels 5246/5247)
                 |
[ Lightweight Access Points (LAPs) ]
     |             |             |
[ Client 1 ]  [ Client 2 ]  [ Client 3 ]
```

### 3.1 Wi-Fi Standards Matrix

| Standard | Commercial Name | Frequencies | Max Physical Rate | Modulation | Key Innovations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **802.11ac** | Wi-Fi 5 | $5\,\text{GHz}$ | $6.9\,\text{Gbps}$ | 256-QAM | Downlink MU-MIMO |
| **802.11ax** | Wi-Fi 6 / 6E | $2.4 / 5 / 6\,\text{GHz}$ | $9.6\,\text{Gbps}$ | 1024-QAM | OFDMA, Uplink/Downlink MU-MIMO, Target Wake Time (TWT), BSS Coloring |
| **802.11be** | Wi-Fi 7 | $2.4 / 5 / 6\,\text{GHz}$ | $46\,\text{Gbps}$ | 4096-QAM | $320\,\text{MHz}$ Channels, Multi-Link Operation (MLO), 16x16 MU-MIMO |
