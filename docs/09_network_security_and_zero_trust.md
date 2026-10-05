# TRACK 09 // NETWORK SECURITY, IPsec VPNs, FIREWALLS & ZERO TRUST

```
================================================================================
  SPECIFICATION: RFC 4301 (IPsec) | RFC 7296 (IKEv2) | NIST SP 800-207 (Zero Trust)
  THEME: Stateful vs NGFW, IPsec Phase 1/2, 802.1X RADIUS, MACsec, Microsegmentation
  COMPLIANCE: ZERO EMOJIS // SECURITY ARCHITECTURE COMPENDIUM
================================================================================
```

---

## 1. Firewall Architecture & Inspection Mechanics

```
+-------------------------------------------------------------------------------+
|                      FIREWALL GENERATION MATRIX                               |
+-------------------------------------------------------------------------------+
| Generation  | Type              | OSI Inspection Scope  | Deep Context        |
+-------------+-------------------+-----------------------+---------------------+
| Gen 1       | Stateless ACL     | L3 (IP) + L4 (Ports)  | None (Per-packet)   |
| Gen 2       | Stateful (SPI)    | L3, L4 + State Table  | Tracks TCP Handshake|
| Gen 3       | Next-Gen (NGFW)   | L3 - L7 Full Payload  | App-ID, User-ID, SSL|
+-------------------------------------------------------------------------------+
```

### 1.1 Next-Generation Firewall (NGFW) Inspection Pipeline

```
Raw Ingress Packet
  --> L2/L3 Routing & Zone Determination (Trust -> Untrust)
  --> Stateful Session Lookup (Connection Tracker table)
  --> SSL/TLS Hardware Decryption (Forward Proxy / Inbound Inspection)
  --> App-ID Engine (Layer 7 Protocol Heuristics & Signature matching)
  --> User-ID Engine (802.1X / Active Directory Kerberos mapping)
  --> Threat Prevention Engine (IPS, Anti-Virus, DNS Security, Sandbox)
  --> NAT & Egress Route Processing
```

---

## 2. IPsec VPN Architecture (IKEv1 / IKEv2 / ESP / AH)

```
[ Branch Gateway: 203.0.113.1 ]                     [ HQ Gateway: 198.51.100.1 ]
              |                                                   |
              +==== ENCRYPTED IPSEC ESP TUNNEL (UDP 500/4500) ====+
              |                                                   |
[ LAN: 10.1.0.0/24 ]                                [ LAN: 10.2.0.0/24 ]
```

### 2.1 IKEv2 (Internet Key Exchange v2 / RFC 7296) Handshake

```
Initiator (Branch)                                     Responder (HQ)
    |                                                         |
    | --- 1. IKE_SA_INIT (Security Proposal, DH PubKey, Nonce) --> |
    | <--- 2. IKE_SA_INIT (Selected Proposal, DH PubKey, Nonce) -- |
    |                                                         |
  [ IKE SA ESTABLISHED: SHARED SECRET COMPUTED VIA ECDH ]
    |                                                         |
    | --- 3. IKE_AUTH {Encrypted: ID_i, Cert/PSK, Child SA} -> |
    | <--- 4. IKE_AUTH {Encrypted: ID_r, Cert/PSK, Child SA} - |
    |                                                         |
  [ IPsec CHILD SA ESTABLISHED: TRAFFIC ENCRYPTION READY (ESP) ]
```

### 2.2 ESP Packet Format (Encapsulating Security Payload / RFC 4303)

```
+---------------+---------------+---------------+---------------+---------------+
| Outer IP (20B)| ESP Hdr (8B)  | Encrypted:    | ESP Trailer   | ESP Auth ICV  |
| New Public IPs| SPI (4B)+Seq# | Inner IP + TCP| Pad + NextHdr | HMAC-SHA256   |
+---------------+---------------+---------------+---------------+---------------+
```

---

## 3. Network Access Control (IEEE 802.1X & RADIUS / EAP-TLS)

```
[ Supplicant (Laptop) ] ======= [ Authenticator (Switch Port) ] ======= [ Authentication Server ]
                                (EAPoL - EAP over LAN)                  (RADIUS / Cisco ISE)
          |                               |                                      |
          | ---- 1. EAPoL-Start --------> |                                      |
          | <--- 2. EAP-Request/Identity- |                                      |
          | ---- 3. EAP-Response/Identity>| ---- 4. RADIUS Access-Request -----> |
          |                               | <--- 5. RADIUS Access-Challenge ---- |
          | <--- 6. EAP-TLS Handshake --- | <--- 7. EAP-TLS Exchanges ---------> |
          |                               |                                      |
          |                               | <--- 8. RADIUS Access-Accept ------- |
          |                               |      (VLAN Assignment, dACL, SGT)    |
          | <--- 9. EAP-Success --------- |                                      |
  [ PORT STATE UNBLOCKED -> TRAFFIC FORWARDING PERMITTED ]
```

---

## 4. Zero Trust Architecture (ZTA / NIST SP 800-207)

```
             +----------------------------------------------------+
             |            CONTROL PLANE: POLICY ENGINE            |
             |  Continuous Trust Evaluation & Risk Scoring Core   |
             +-------------------------+--------------------------+
                                       |
                   +-------------------v--------------------+
                   |         POLICY ENFORCEMENT POINT       |
                   |   (Microsegmentation / App Gateway)    |
                   +-------------------+--------------------+
                                       |
   +-----------------------------------v------------------------------------+
   |                              DATA PLANE                                |
   | [ Authenticated Endpoint ] ---------------> [ Micro-segmented Workload]|
   | (Context: Device Health + Mutual TLS + MFA)  (Strict Explicit Policy)  |
   +------------------------------------------------------------------------+
```

### Core Zero Trust Principles
1. **Never Trust, Always Verify**: Perimeter location (internal vs. external) grants zero implicit trust.
2. **Least Privilege Access**: Access is restricted per-session, per-application, using explicit dynamic context.
3. **Assume Breach**: Inspect and log all traffic continuously; partition network into micro-segments to prevent lateral movement.
