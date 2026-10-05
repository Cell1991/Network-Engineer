# TRACK 05 // TRANSPORT LAYER, TCP STATE DYNAMICS & CONGESTION CONTROL

```
================================================================================
  SPECIFICATION: RFC 793 / RFC 9293 (TCP) | RFC 768 (UDP) | RFC 9000 (QUIC)
  THEME: TCP 3-Way Handshake, Sliding Windows, SACK, BBR/CUBIC Congestion, QUIC
  COMPLIANCE: ZERO EMOJIS // RIGOROUS PROTOCOL REFERENCE
================================================================================
```

---

## 1. TCP Segment Header Specification (RFC 9293)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |           |U|A|P|R|S|F|                               |
| Offset| Reserved  |R|C|S|S|Y|I|            Window             |
|       |           |G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |        Urgent Pointer         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 1.1 TCP Control Flags

- **URG (0x20)**: Urgent pointer field is significant.
- **ACK (0x10)**: Acknowledgment field is significant. (Present on all packets after initial SYN).
- **PSH (0x08)**: Push function; tells receiver buffer to immediately deliver data to application layer.
- **RST (0x04)**: Abruptly resets the connection.
- **SYN (0x02)**: Synchronize sequence numbers; initiates connection.
- **FIN (0x01)**: No more data from sender; initiates graceful connection closure.
- **ECE (0x40)** / **CWR (0x80)**: RFC 3168 Explicit Congestion Notification flags.

---

## 2. TCP 3-Way Handshake & 4-Way Teardown Sequence

```
CLIENT (Initiator)                               SERVER (Listener)
      |                                                 |
      | -------- 1. SYN (Seq=ISN_c, Win=65535, MSS=1460) -> | [State: SYN_RECEIVED]
      |                                                 |
[State: SYN_SENT]                                       |
      | <------- 2. SYN+ACK (Seq=ISN_s, Ack=ISN_c+1) -- |
      |                                                 |
[State: ESTABLISHED]                                    |
      | -------- 3. ACK (Seq=ISN_c+1, Ack=ISN_s+1) ---> | [State: ESTABLISHED]
      |                                                 |
      | === BIDIRECTIONAL FULL-DUPLEX BYTE STREAM ===   |
      |                                                 |
      | -------- 4. FIN (Seq=u, Ack=v) ---------------> | [State: CLOSE_WAIT]
[State: FIN_WAIT_1]                                     |
      | <------- 5. ACK (Seq=v, Ack=u+1) -------------- |
[State: FIN_WAIT_2]                                     |
      | <------- 6. FIN (Seq=w, Ack=u+1) -------------- | [State: LAST_ACK]
      |                                                 |
      | -------- 7. ACK (Seq=u+1, Ack=w+1) -----------> | [State: CLOSED]
[State: TIME_WAIT (2*MSL = 60s-120s)]                  |
      |                                                 |
[State: CLOSED]                                         |
```

---

## 3. TCP Sliding Window & Flow Control

Flow control ensures a fast sender does not overwhelm a slow receiver's buffer:

$$\text{Effective Window} = \min(\text{Congestion Window } [CWND], \text{Advertised Receive Window } [RWND])$$

```
Sender Buffer:
[ 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 ]
  |___________|   |______________________|   |______________|
   Sent & ACKed     Sent, Not Yet ACKed       Can Send Now (Window)
```

- **TCP Window Scale Option (RFC 7323)**: Extends maximum receive window from $65,535\,\text{bytes}$ ($64\,\text{KB}$) up to $1\,\text{GB}$ ($2^{30}$) using a scale factor exponent ($0 - 14$).
- **Selective Acknowledgement (SACK / RFC 2018)**: Allows receiver to inform sender of discontinuous out-of-order blocks received, retransmitting only lost segments instead of the entire window (Go-Back-N).

---

## 4. Modern TCP Congestion Control Algorithms

```
+-------------------------------------------------------------------------------+
|                      CONGESTION CONTROL ALGORITHM MATRIX                      |
+-------------------------------------------------------------------------------+
| Algorithm   | Signal Trigger    | Window Dynamics       | Target Scenario     |
+-------------+-------------------+-----------------------+---------------------+
| TCP Reno    | Packet Loss       | AIMD (Additive Inc /  | Legacy / Standard   |
|             | (Duplicate ACKs)  | Multiplicative Dec)   | Loss-based networks |
+-------------+-------------------+-----------------------+---------------------+
| TCP Cubic   | Packet Loss       | $W(t) = C(t-K)^3+W_{\max}$ | Linux Default (Long |
|             |                   | Cubic Growth Curve    | Fat Networks - LFN) |
+-------------+-------------------+-----------------------+---------------------+
| TCP BBR     | RTT & Max Delivery| Max Bandwidth +       | Google WAN / YouTube|
| (v1/v2/v3)  | Rate (Model-based)| Min RTT Polling       | Bufferbloat Immune  |
+-------------------------------------------------------------------------------+
```

### 4.1 BBR (Bottleneck Bandwidth and Round-trip propagation time)

Unlike loss-based algorithms (Reno, Cubic) that blindly increase window until queues overflow and packet drops occur, BBR continuously measures:
1. **Bottleneck Bandwidth ($\text{BtlBw}$)**: Maximum delivery rate over recent time windows.
2. **Round-Trip Propagation Time ($\text{RTprop}$)**: Minimum observed physical RTT.

$$\text{Optimal In-Flight Bytes (BDP)} = \text{BtlBw} \times \text{RTprop}$$

BBR paces packet injection to match physical bottleneck bandwidth exactly, maintaining empty router queues and preventing bufferbloat.

---

## 5. UDP & QUIC / HTTP/3 Architecture (RFC 9000)

```
[ Traditional Stack ]               [ Modern QUIC Stack ]
+---------------------+             +---------------------+
| HTTP/2              |             | HTTP/3              |
+---------------------+             +---------------------+
| TLS 1.3             |             | QUIC (Encrypted)    |
+---------------------+             | - Stream Mux        |
| TCP (Stream)        |             | - Loss Recovery     |
+---------------------+             +---------------------+
| IP                  |             | UDP                 |
+---------------------+             +---------------------+
```

### 5.1 QUIC Advantages over TCP

1. **Zero RTT Connection Establishment (0-RTT / 1-RTT)**: Merges transport and cryptographic handshakes into a single round-trip.
2. **Head-of-Line Blocking Elimination**: Multi-stream multiplexing within a single UDP session. Packet loss on Stream A does not stall Stream B.
3. **Connection Migration (Mobility)**: Connections identified by a 64-bit **Connection ID (CID)** rather than 4-tuple (IP:Port), allowing seamless handoff between Wi-Fi and 5G cellular networks without dropping active sessions.
