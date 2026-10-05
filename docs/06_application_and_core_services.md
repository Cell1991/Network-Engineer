# TRACK 06 // APPLICATION LAYER PROTOCOLS & CORE NETWORK SERVICES

```
================================================================================
  SPECIFICATION: RFC 1035 (DNS) | RFC 2131 (DHCP) | RFC 8446 (TLS 1.3) | RFC 5321
  THEME: DNS Resolution Trees, DHCP DORA Exchanges, TLS 1.3 Handshake, SNMPv3
  COMPLIANCE: ZERO EMOJIS // TECHNICAL FIELD MANUAL
================================================================================
```

---

## 1. DNS Architecture & Iterative Resolution Engine (RFC 1035)

The Domain Name System (DNS) operates on UDP/TCP Port 53, providing hierarchical distributed domain name translation.

```
                  [ ROOT HINT SERVERS: . (13 Clusters A-M) ]
                                    |
                    [ TLD SERVERS: .com, .org, .net ]
                                    |
                 [ AUTHORITATIVE SERVERS: example.com ]
                                    |
                [ LOCAL RECURSIVE RESOLVER: 1.1.1.1 ]
                                    |
                            [ CLIENT BROWSER ]
```

### 1.1 Step-by-Step Recursive vs. Iterative Query Flow

```
Client             Recursive Resolver          Root Server       TLD Server       Auth Server
  |                         |                       |                 |                |
  | -- 1. Query example.com -> |                    |                 |                |
  |                         | -- 2. Query . ------> |                 |                |
  |                         | <- 3. Referral .com - |                 |                |
  |                         |                                         |                |
  |                         | -- 4. Query .com ---------------------> |                |
  |                         | <- 5. Referral ns1.example.com -------- |                |
  |                         |                                                          |
  |                         | -- 6. Query example.com -------------------------------> |
  |                         | <- 7. Return A Record (93.184.216.34) ------------------ |
  |                         |
  | <- 8. Return IP Cache --|
```

### 1.2 DNS Resource Record (RR) Taxonomy

- **A**: IPv4 Host Address (32 bits).
- **AAAA**: IPv6 Host Address (128 bits).
- **CNAME**: Canonical Name alias pointer.
- **MX**: Mail Exchange record with preference priority.
- **PTR**: Pointer record for reverse DNS IP-to-domain lookups (`in-addr.arpa`).
- **TXT / SPF / DKIM / DMARC**: Arbitrary text attributes used for domain ownership validation and anti-spoofing email cryptographic authentication.
- **NS**: Authoritative Name Server record.
- **SOA**: Start of Authority (Serial number, Refresh, Retry, Expire, Minimum TTL).

---

## 2. Dynamic Host Configuration Protocol (DHCPv4 / DHCPv6)

### 2.1 DHCPv4 4-Way DORA Handshake

```
CLIENT (0.0.0.0:68)                                   DHCP SERVER (IP:67)
      |                                                        |
      | -------- 1. DHCP DISCOVER (Broadcast L2/L3) ---------> |
      |          Src: 0.0.0.0:68 | Dst: 255.255.255.255:67     |
      |                                                        |
      | <------- 2. DHCP OFFER (Unicast/Broadcast) ----------- |
      |          Offered IP: 192.168.1.50 | Lease: 86400s      |
      |                                                        |
      | -------- 3. DHCP REQUEST (Broadcast) ----------------> |
      |          Accepts Offer from Server X                   |
      |                                                        |
      | <------- 4. DHCP ACK (Unicast/Broadcast) ------------- |
      |          Assigns IP, Subnet Mask, Default GW, DNS      |
```

### 2.2 DHCP Relay Agent (IP Helper-Address / Option 82)

When DHCP client and DHCP server reside on different subnets/VLANs, the default gateway router intercepts broadcast DISCOVER packets, wraps them in unicast UDP, and relays them to the centralized DHCP server:

```cisco
interface GigabitEthernet0/0/1
 description USER-VLAN-10-GATEWAY
 ip address 192.168.10.1 255.255.255.0
 ip helper-address 10.100.0.50
 ip dhcp relay information option
```

---

## 3. Cryptographic Handshake Architecture (TLS 1.3 / RFC 8446)

TLS 1.3 reduces the handshake from 2 round-trips (TLS 1.2) to **1-RTT**, while mandating Forward Secrecy (Ephemeral Diffie-Hellman) and encrypting certificate exchanges.

```
CLIENT                                                          SERVER
  |                                                               |
  | --- ClientHello (Supported Ciphers, KeyShare [ECDH Pub]) ---> |
  |                                                               |
  | <--- ServerHello (Selected Cipher, KeyShare [ECDH Pub]) ----- |
  | <--- {EncryptedExtensions} ---------------------------------- |
  | <--- {Certificate} ------------------------------------------ |
  | <--- {CertificateVerify} ------------------------------------ |
  | <--- {Finished} --------------------------------------------- |
  |                                                               |
  | === [KEYS COMPUTED: FULLY ENCRYPTED 1-RTT SECURE CHANNEL] === |
  |                                                               |
  | --- {Finished} ---------------------------------------------> |
  | --- {HTTP/2 or HTTP/3 Encrypted Request} -------------------> |
  | <--- {HTTP/2 or HTTP/3 Encrypted Response} ------------------ |
```

---

## 4. Network Management (SNMPv3 Architecture / RFC 3411)

```
+-------------------------------------------------------------------------------+
|                      SNMP PROTOCOL SECURITY EVOLUTION                         |
+-------------------------------------------------------------------------------+
| Version   | Authentication            | Privacy (Encryption)  | Integrity     |
+-----------+---------------------------+-----------------------+---------------+
| SNMPv1    | Plaintext Community String| None (Plaintext)      | None          |
| SNMPv2c   | Plaintext Community String| None (Plaintext)      | None          |
| SNMPv3    | HMAC-SHA-256 / SHA-512    | AES-128 / AES-256     | Cryptographic |
+-------------------------------------------------------------------------------+
```

### SNMPv3 Security Models (USM: User-based Security Model)
- `noAuthNoPriv`: No authentication, no encryption (unsecure).
- `authNoPriv`: Cryptographic authentication (SHA-256), plaintext MIB polling.
- `authPriv`: Cryptographic authentication (SHA-256) AND payload encryption (AES-256).
