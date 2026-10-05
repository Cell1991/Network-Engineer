# TRACK 02 // DATA LINK LAYER, ETHERNET SWITCHING & IEEE 802 STANDARDS

```
================================================================================
  SPECIFICATION: IEEE 802.1D / 802.1w / 802.1s / 802.1Q / 802.3ad LACP
  THEME: Frame Formats, Spanning Tree Convergence, VLAN Tagging, VXLAN
  COMPLIANCE: ZERO EMOJIS // TECHNICAL SPECIFICATION
================================================================================
```

---

## 1. Ethernet II Frame Format (RFC 894 / IEEE 802.3)

An Ethernet II frame encapsulates Network Layer packets (IPv4, IPv6, ARP) for transmission across a local broadcast domain.

```
+-------------------------------------------------------------------------------+
| 7 Bytes  | 1 Byte |  6 Bytes  |  6 Bytes  |  2 Bytes   | 46-1500 B | 4 Bytes  |
| Preamble |  SFD   |  Dst MAC  |  Src MAC  | EtherType  |  Payload  |   FCS    |
| (1010..) |(1010..)| (6 Octets)| (6 Octets)|  (0x0800)  |  (IPv4)   |  (CRC32) |
+-------------------------------------------------------------------------------+
```

### 1.1 Field Breakdown

1. **Preamble (7 Bytes)**: Alternating bit pattern (`10101010` x 7) to synchronize receiver clock PLLs.
2. **SFD (Start Frame Delimiter, 1 Byte)**: Pattern `10101011` marking the immediate start of the destination MAC.
3. **Destination MAC (6 Bytes / 48 bits)**:
   - Bit 0 of Octet 0 (I/G Bit): `0` = Unicast, `1` = Multicast/Broadcast.
   - Bit 1 of Octet 0 (U/L Bit): `0` = Globally Unique (OUI), `1` = Locally Administered.
4. **Source MAC (6 Bytes / 48 bits)**: Hardware address of transmitting interface.
5. **EtherType (2 Bytes)**:
   - `0x0800`: IPv4
   - `0x86DD`: IPv6
   - `0x0806`: ARP
   - `0x8100`: IEEE 802.1Q VLAN Tagged Frame
   - `0x88A8`: IEEE 802.1ad Service VLAN Tag (QinQ Outer Tag)
6. **Payload (46 - 1500 Bytes)**: Data payload. If payload $< 46$ bytes, padding is appended to satisfy minimum 64-byte frame length requirement (for CSMA/CD slot time).
7. **FCS (Frame Check Sequence, 4 Bytes)**: 32-bit Cyclic Redundancy Check (CRC-32) computed over Dst MAC, Src MAC, EtherType, and Payload.

---

## 2. IEEE 802.1Q VLAN Tagging & QinQ Architecture

### 2.1 802.1Q Tag Structure (4 Bytes)

```
+---------------------------------------------------------------------------+
| 2 Bytes (16 bits) | 3 bits | 1 bit |        12 bits (VID 0 - 4095)        |
|  TPID (0x8100)    |  PCP   |  DEI  |  VLAN ID (1-4094 usable)             |
+---------------------------------------------------------------------------+
```

- **TPID (Tag Protocol Identifier)**: `0x8100` identifies frame as 802.1Q tagged.
- **PCP (Priority Code Point, 3 bits)**: IEEE 802.1p Quality of Service priority (Class of Service 0-7).
- **DEI (Drop Eligible Indicator, 1 bit)**: When `1`, frame can be discarded during buffer congestion.
- **VID (VLAN Identifier, 12 bits)**:
  - `0`: Priority-tagged frame (carries CoS only).
  - `1`: Default administrative VLAN.
  - `2 - 4094`: Usable VLAN identifiers.
  - `4095`: Reserved for internal implementation.

### 2.2 IEEE 802.1ad Double Tagging (QinQ)

Service Providers encapsulate customer VLAN-tagged frames inside an outer Service Provider VLAN (S-VLAN):

```
+-----------+-----------+---------------+---------------+---------------+
| Dst / Src | S-Tag     | C-Tag         | EtherType     | Payload       |
| MAC (12B) | (TPID 88A8| (TPID 8100    | (0x0800 IPv4) |               |
|           |  S-VID)   |  C-VID)       |               |               |
+-----------+-----------+---------------+---------------+---------------+
```

---

## 3. Spanning Tree Protocol Family (STP / RSTP / MSTP)

```
+-------------------------------------------------------------------------------+
|                      STP PROTOCOL CONVERGENCE EVOLUTION                       |
+-------------------------------------------------------------------------------+
| Standard      | Convergence Time  | Instances     | Port States               |
+---------------+-------------------+---------------+---------------------------+
| STP (802.1D)  | 30 - 50 Seconds   | 1 (CST)       | Block, Listen, Learn, Fwd |
| PVST+ (Cisco) | 30 - 50 Seconds   | 1 per VLAN    | Block, Listen, Learn, Fwd |
| RSTP (802.1w) | < 1 Second        | 1 (CST)       | Discarding, Learning, Fwd |
| Rapid-PVST+   | < 1 Second        | 1 per VLAN    | Discarding, Learning, Fwd |
| MSTP (802.1s) | < 1 Second        | Mapped Groups | Discarding, Learning, Fwd |
+-------------------------------------------------------------------------------+
```

### 3.1 802.1D / 802.1w Convergence Mechanics

```
                 [ ROOT BRIDGE (Priority 4096) ]
                           /        \
                   DP (Cost 4)    DP (Cost 4)
                         /            \
                       RP              RP
              [ SWITCH 02 ] --------- [ SWITCH 03 ]
                   DP                  ALTERNATE (BLOCKING)
                                       (Loop Eliminated)
```

1. **Root Bridge Election**:
   - Every bridge advertises its Bridge ID: `Bridge ID = Priority (16b) + MAC (48b)`.
   - Lowest Bridge ID wins globally. Default Priority: 32768 (configured in increments of 4096).
2. **Root Port (RP) Selection** (1 per non-root switch):
   - Port with the lowest cumulative **Root Path Cost (RPC)** to the Root Bridge.
   - Tiebreaker 1: Lowest sender Bridge ID.
   - Tiebreaker 2: Lowest sender Port Priority and Port Number.
3. **Designated Port (DP) Selection** (1 per collision segment/link):
   - Port on the bridge that offers the lowest Root Path Cost for that link.
4. **Alternate / Backup Port (AP/BP)**:
   - Remaining ports are placed in `BLOCKING` / `DISCARDING` state to prevent broadcast storms.

### 3.2 RSTP Port Roles & Rapid Proposal-Agreement Handshake

Instead of waiting for 802.1D Forward Delay timers ($2 \times 15\,\text{s} = 30\,\text{s}$), RSTP uses an explicit point-to-point handshake:

```
Switch A (Root)                          Switch B
   |                                        |
   | --- Proposal (RSTP BPDU Flags: 0x3C)-> |  (B puts non-edge ports into Discarding)
   |                                        |  (B syncs topology)
   | <-- Agreement (RSTP BPDU Flags: 0x7C)- |  (B immediately moves port to Forwarding)
   |                                        |
 [ Port Forwarding in < 10ms ]
```

---

## 4. Link Aggregation Control Protocol (IEEE 802.3ad / 802.1AX LACP)

LACP bundles multiple physical Ethernet links into a single logical channel (Port-Channel / LAG) for increased bandwidth and link-level failover.

```
[ Switch A ] ================================= [ Switch B ]
  Port 1  --- (LACP DU Heartbeats: 1s or 30s) --- Port 1
  Port 2  --------------------------------------- Port 2
  Port 3  --------------------------------------- Port 3
  Port 4  --------------------------------------- Port 4
  Logical Aggregate: Port-Channel 1 (40 Gbps Capacity)
```

### 4.1 Traffic Distribution & Hash Algorithms

Frames are distributed across LAG member links using a deterministic hash polynomial:
$$\text{Egress Port Index} = \text{Hash}(\text{Src IP}, \text{Dst IP}, \text{Src Port}, \text{Dst Port}) \pmod N$$
This preserves per-flow packet sequencing without causing TCP out-of-order retransmissions.

---

## 5. VXLAN (Virtual Extensible LAN / RFC 7348)

VXLAN is an L2-over-L3 overlay encapsulation protocol that encapsulates standard Ethernet frames inside UDP packets (Port 4789).

```
+-------------------+---------------+---------------+---------------+---------------+
| Outer Eth (14B)   | Outer IP (20B)| Outer UDP(8B) | VXLAN Hdr(8B) | Inner Frame   |
| Dst/Src Underlay  | Underlay VTEP | Dst Port 4789 | VNI (24 bits) | Original L2   |
| MAC Addresses     | IP Addresses  | Source = Hash | 16 Million IDs| Customer Frame|
+-------------------+---------------+---------------+---------------+---------------+
```

- **VNI (VXLAN Network Identifier, 24 bits)**: Expands VLAN limit from 4,094 to 16,777,216 distinct overlay broadcast domains.
- **VTEP (VXLAN Tunnel Endpoint)**: Switch ASIC or hypervisor entity performing encapsulation/decapsulation.

---

## 6. Enterprise Configuration Directives

### Cisco IOS-XE Switching Configuration

```cisco
! Configure LACP Port-Channel Trunk with 802.1Q Allowed List
interface Port-channel1
 description UPLINK-TO-CORE-FABRIC
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30,100
 switchport trunk native vlan 999
 spanning-tree guard root
!
interface Range GigabitEthernet0/1/0 - 1
 description LACP-BUNDLE-MEMBERS
 channel-group 1 mode active
!
! RSTP Configuration
spanning-tree mode rapid-pvst
spanning-tree vlan 10,20 priority 4096
spanning-tree portfast default
spanning-tree portfast bpduguard default
```
