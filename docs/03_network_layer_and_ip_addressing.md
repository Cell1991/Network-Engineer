# TRACK 03 // NETWORK LAYER, IPv4/IPv6 ADDRESSING & PACKET STRUCTURES

```
================================================================================
  SPECIFICATION: RFC 791 (IPv4) | RFC 8200 (IPv6) | RFC 4632 (CIDR) | RFC 3021
  THEME: Binary Subnetting, VLSM Partitioning, SLAAC EUI-64, NAT/PAT & ICMP
  COMPLIANCE: ZERO EMOJIS // TECHNICAL BLUEPRINT
================================================================================
```

---

## 1. IPv4 Packet Header Specification (RFC 791)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |        Header Checksum        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source IP Address                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination IP Address                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 1.1 Bit Field Definitions

- **Version (4 bits)**: Always `4` (`0100`).
- **IHL (Internet Header Length, 4 bits)**: Number of 32-bit words in header (minimum `5` = 20 bytes, max `15` = 60 bytes).
- **Type of Service / DSCP + ECN (8 bits)**:
  - DSCP (6 bits): Differentiated Services Code Point (e.g., EF=46, AF41=34, CS0=0).
  - ECN (2 bits): Explicit Congestion Notification (00: Not-ECT, 01: ECT(1), 10: ECT(0), 11: CE [Congestion Encountered]).
- **Total Length (16 bits)**: Entire packet length in bytes (max 65,535 bytes).
- **Identification (16 bits)**: Unique identifier for assembling fragmented packets.
- **Flags (3 bits)**:
  - Bit 0: Reserved (must be 0).
  - Bit 1: **DF (Don't Fragment)**. If packet exceeds link MTU and DF=1, router drops packet and returns ICMP Type 3 Code 4.
  - Bit 2: **MF (More Fragments)**. `1` indicates additional fragments follow; `0` indicates last fragment.
- **Fragment Offset (13 bits)**: Position of fragment payload in 8-byte (64-bit) units relative to original unfragmented payload.
- **Time to Live (TTL, 8 bits)**: Decremented by 1 at each L3 router hop. Drops at 0 (returns ICMP Type 11 Time Exceeded) to prevent routing loops.
- **Protocol (8 bits)**:
  - `1`: ICMP
  - `2`: IGMP
  - `6`: TCP
  - `17`: UDP
  - `47`: GRE
  - `50`: IPsec ESP
  - `51`: IPsec AH
  - `89`: OSPF
- **Header Checksum (16 bits)**: RFC 1071 16-bit One's Complement sum over header fields. Recalculated at every router hop due to TTL decrement.

---

## 2. Binary Subnetting & CIDR Calculation Mathematics

### 2.1 Complete CIDR Reference Table

| CIDR | Subnet Mask | Wildcard Mask | Total Addresses | Usable Hosts |
| :--- | :--- | :--- | :--- | :--- |
| **/32** | 255.255.255.255 | 0.0.0.0 | 1 | 1 (Host Route / Loopback) |
| **/31** | 255.255.255.254 | 0.0.0.1 | 2 | 2 (RFC 3021 Point-to-Point) |
| **/30** | 255.255.255.252 | 0.0.0.3 | 4 | 2 (Legacy Point-to-Point) |
| **/29** | 255.255.255.248 | 0.0.0.7 | 8 | 6 |
| **/28** | 255.255.255.240 | 0.0.0.15 | 16 | 14 |
| **/27** | 255.255.255.224 | 0.0.0.31 | 32 | 30 |
| **/26** | 255.255.255.192 | 0.0.0.63 | 64 | 62 |
| **/25** | 255.255.255.128 | 0.0.0.127 | 128 | 126 |
| **/24** | 255.255.255.0 | 0.0.0.255 | 256 | 254 |
| **/23** | 255.255.254.0 | 0.0.1.255 | 512 | 510 |
| **/22** | 255.255.252.0 | 0.0.3.255 | 1,024 | 1,022 |
| **/20** | 255.255.240.0 | 0.0.15.255 | 4,096 | 4,094 |
| **/16** | 255.255.0.0 | 0.0.255.255 | 65,536 | 65,534 |
| **/8**  | 255.0.0.0 | 0.255.255.255 | 16,777,216 | 16,777,214 |

---

## 3. IPv6 Architecture & Address Mechanics (RFC 8200)

### 3.1 Fixed 40-Byte Base Header

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version| Traffic Class |           Flow Label                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Payload Length        |  Next Header  |   Hop Limit   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+                         Source Address                        +
|                           (128 bits)                          |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+                      Destination Address                      +
|                           (128 bits)                          |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 3.2 IPv6 Address Types & Scopes

```
+-------------------------------------------------------------------------------+
| Address Scope     | Prefix / Range          | Description                     |
+-------------------+-------------------------+---------------------------------+
| Unspecified       | ::/128                  | Used before address assignment  |
| Loopback          | ::1/128                 | Equivalent to 127.0.0.1         |
| Link-Local        | fe80::/10               | Non-routable local segment only |
| Unique Local(ULA) | fc00::/7 (fd00::/8)     | RFC 4193 Private IPv6 addresses |
| Global Unicast    | 2000::/3                | Routable Internet IPv6 addresses|
| Multicast (All)   | ff02::1                 | All nodes on local link         |
| Multicast (Rtrs)  | ff02::2                 | All routers on local link       |
| Multicast (OSPF)  | ff02::5, ff02::6        | OSPFv3 All / DR Routers         |
+-------------------------------------------------------------------------------+
```

### 3.3 Modified EUI-64 Identifier Derivation

```
MAC Address: 00:1A:2B:3C:4D:5E (48 bits)
Step 1: Split into two 24-bit halves: [00:1A:2B] and [3C:4D:5E]
Step 2: Insert 0xFFFE in the center : 00:1A:2B:FF:FE:3C:4D:5E
Step 3: Invert Bit 7 (U/L Bit) of Octet 0:
        0x00 = 0000 0000_2  --> Invert 7th bit: 0000 0010_2 = 0x02
Resulting EUI-64: 021a:2bff:fe3c:4d5e
Link-Local Address: fe80::21a:2bff:fe3c:4d5e
```

---

## 4. NAT / PAT (Network Address Translation)

```
[ Private LAN: 192.168.1.50:52410 ] 
             |
   (Ingress to Gateway)
             |
[ NAT Router NAT Table ]
  Inside Local  : 192.168.1.50:52410
  Inside Global : 203.0.113.5:60001
  Outside Global: 93.184.216.34:443
             |
   (Egress to Public WAN)
             |
[ Public Web Server: 93.184.216.34:443 ]
```

### 4.1 NAT Flavors

1. **Static NAT**: 1-to-1 permanent IP mapping (typically for DMZ public servers).
2. **Dynamic NAT**: Pool of public IPs mapped dynamically to internal hosts.
3. **PAT (Port Address Translation / NAT Overload)**: Many-to-1 mapping using dynamic L4 source port multiplexing (up to 64,512 concurrent translation state sessions per public IP).
