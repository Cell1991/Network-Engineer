# TRACK 11 // NETWORK OBSERVABILITY, TELEMETRY & SYSTEMATIC TROUBLESHOOTING

```
================================================================================
  SPECIFICATION: gNMI (gRPC Network Management Interface) | NetFlow v9 | IPFIX
  THEME: Streaming Telemetry, Flow Records, Wireshark Packet Forensics, MTU Bugs
  COMPLIANCE: ZERO EMOJIS // NOC TROUBLESHOOTING RUNBOOK
================================================================================
```

---

## 1. Network Telemetry Evolution: SNMP Polling vs. Push Telemetry

```
+-------------------------------------------------------------------------------+
|                      MONITORING ARCHITECTURE COMPARISON                       |
+-------------------------------------------------------------------------------+
| Parameter     | Legacy SNMP Polling           | Streaming Telemetry (gNMI)    |
+---------------+-------------------------------+-------------------------------+
| Model         | Pull (NMS queries periodically)| Push (Device streams metrics) |
| Cadence       | 5 - 15 Minutes                | Sub-second (100ms - 1s)       |
| Data Format   | MIB / OID Numeric Trees       | OpenConfig YANG Structured    |
| Transport     | UDP Port 161 (Unencrypted)    | gRPC / HTTP/2 over TLS (mTLS) |
| CPU Overhead  | High periodic CPU spikes      | Low continuous hardware push  |
| Granularity   | Averaged counters             | Real-time microburst detection|
+-------------------------------------------------------------------------------+
```

---

## 2. Flow Telemetry (NetFlow v9 & IPFIX / RFC 7011)

Flow records track conversations across interfaces based on 7-key tuples:
1. Source IP Address
2. Destination IP Address
3. Source Port
4. Destination Port
5. Layer 3 Protocol
6. Ingress Interface
7. IP Type of Service (ToS / DSCP)

```
[ Ingress Packets ] ---> [ Flow Cache Engine ] ---> [ Flow Export Template ]
                              |                            |
                         (Aggregates Bytes,          (UDP Export to
                          Packets, Duration)          Collector: Port 2055)
```

---

## 3. Systematic OSI Troubleshooting Methodology

```
+-------------------------------------------------------------------------------+
| METHODOLOGY     | DIRECTION   | STARTING POINT                                |
+-----------------+-------------+-----------------------------------------------+
| Bottom-Up       | L1 -> L7    | Physical Link, SFP LEDs, Cabling, Duplex      |
| Top-Down        | L7 -> L1    | Application Health, DNS Resolution, SSL Certs |
| Divide-and-Conq | L3/L4 Center| Ping / Traceroute to isolate segment          |
+-------------------------------------------------------------------------------+
```

### 3.1 Systematic OSI Layer Troubleshooting Checklist

```
[ L1 PHYSICAL ]
  --> Check interface status: 'show interfaces status' (Connected vs Notconnect)
  --> Check optical levels: 'show interfaces transceiver detail' (TX/RX dBm)
  --> Check cable CRC / input errors: 'show interfaces' (Input errors, CRC)

[ L2 DATA LINK ]
  --> Check MAC learning: 'show mac address-table address <MAC>'
  --> Check VLAN assignment: 'show vlan id <VID>' (Port member list)
  --> Check STP state: 'show spanning-tree vlan <VID>' (Forwarding vs Blocking)
  --> Check ARP table: 'show ip arp' or 'arp -a' (Resolves IP to MAC?)

[ L3 NETWORK ]
  --> Check IP & Subnet Mask: 'show ip interface brief'
  --> Check Routing Table: 'show ip route <Destination_IP>' (LPM match?)
  --> Check MTU consistency: 'ping <IP> size 1500 df-bit' (MTU blackhole?)

[ L4 TRANSPORT ]
  --> Check TCP handshake: 'telnet <IP> <Port>' or 'nc -zv <IP> <Port>'
  --> Check firewall session table: 'show conn' (SYN sent, ACK received?)

[ L7 APPLICATION ]
  --> Check DNS resolution: 'nslookup domain.com' or 'dig domain.com'
  --> Check TLS Certificate: 'openssl s_client -connect domain.com:443'
```

---

## 4. MTU / MSS Mismatch & Path MTU Discovery (PMTUD) Blackholes

```
[ Client (MTU 1500) ] === [ GRE/IPsec VPN (MTU 1400) ] === [ Web Server (MTU 1500) ]
        |                              |                              |
        | --- 1. TCP SYN (MSS=1460) -> | ---------------------------> |
        | <--------------------------- | <--- 2. TCP SYN-ACK -------- |
        | --- 3. ACK (Handshake OK) -> | ---------------------------> |
        |                                                             |
        |                                                             |
        |                              | <-- 4. 1500-byte Data Frame- |
        |                              |     (Exceeds Tunnel MTU 1400)|
        |                              |     (DF Bit = 1)             |
        |                              |                              |
        |                              | [ PACKET DROPPED BY ROUTER ] |
        |                              | --> ICMP Type 3 Code 4 ----> |
        |                              |     (Destination Unreachable)|
        |                              |                              |
        |                              | [ IF FIREWALL DROPS ICMP: ]  |
        |                              | [ CONNECTION HANGS FOREVER ] |
        |                              | [ (PMTUD BLACKHOLE BUG)    ] |
```

### Remediation: TCP MSS Clamping
Routers clamp the Maximum Segment Size (MSS) option in passing TCP SYN packets to fit the bottleneck tunnel MTU:

```cisco
interface Tunnel1
 ip mtu 1400
 ip tcp adjust-mss 1360
```
