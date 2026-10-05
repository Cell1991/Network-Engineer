# TRACK 01 // PHYSICAL LAYER, TRANSMISSION MEDIA & HARDWARE INTERFACES

```
================================================================================
  SPECIFICATION: ISO/IEC 7498-1 Layer 1 | IEEE 802.3 Physical Layer Standards
  THEME: Optical Transceivers, Fiber Physics, Copper Modulation & Bit Timing
  COMPLIANCE: ZERO EMOJIS // HIGH-TECH NOC TELEMETRY REFERENCE
================================================================================
```

---

## 1. Physical Layer Theoretical Foundations

The Physical Layer (Layer 1) is responsible for the electrical, optical, and radio frequency transmission of raw, unstructured bit streams across physical communication media. It defines electrical voltages, timing, physical pinouts, cabling impedance, carrier frequencies, and signal modulation techniques.

```
+-----------------------------------------------------------------------------+
|                      PHYSICAL LAYER ENCODING PIPELINE                       |
+-----------------------------------------------------------------------------+
| Bit Stream [010011...]                                                      |
|   --> Line Coding (e.g., NRZ, Manchester, PAM4, 64b/66b)                    |
|   --> Serialization (Parallel bus to serial high-speed differential pairs)  |
|   --> Physical Medium Attachment (PMA) & Medium Dependent Interface (MDI)   |
|   --> Optical Laser / Copper PHY Transmission across Medium                 |
+-----------------------------------------------------------------------------+
```

### 1.1 Fundamental Physical Bounds

#### Nyquist Bit Rate Formula (Noiseless Channel)
For a channel with bandwidth $B$ (in Hertz) and $M$ discrete signal levels:
$$C_{\text{Nyquist}} = 2B \log_2(M) \quad [\text{bits/second}]$$

#### Shannon Capacity Theorem (Noisy Channel)
For a channel operating in the presence of Additive White Gaussian Noise (AWGN) with Signal-to-Noise Ratio (SNR):
$$C_{\text{Shannon}} = B \log_2\left(1 + \frac{S}{N}\right) = B \log_2(1 + 10^{\text{SNR}_{\text{dB}}/10}) \quad [\text{bits/second}]$$

---

## 2. Fiber Optic Physical Infrastructure

### 2.1 Single-Mode Fiber (SMF) vs. Multi-Mode Fiber (MMF)

| Parameter | Single-Mode Fiber (SMF) | Multi-Mode Fiber (MMF) |
| :--- | :--- | :--- |
| **Standard Core Diameter** | $9\,\mu\text{m}$ ($9/125\,\mu\text{m}$) | $50\,\mu\text{m}$ (OM2, OM3, OM4, OM5) or $62.5\,\mu\text{m}$ (OM1) |
| **Cladding Diameter** | $125\,\mu\text{m}$ | $125\,\mu\text{m}$ |
| **Light Source** | Laser Diodes (Distributed Feedback - DFB) | VCSEL (Vertical-Cavity Surface-Emitting Laser) |
| **Operating Wavelengths** | $1310\,\text{nm}$ (O-band), $1550\,\text{nm}$ (C-band) | $850\,\text{nm}$, $953\,\text{nm}$ |
| **Modal Dispersion** | Zero (Single propagating mode) | Significant (Multiple optical propagation modes) |
| **Typical Max Reach** | $10\,\text{km}$ (10GBASE-LR) up to $80\,\text{km}$ (10GBASE-ZR) | $300\,\text{m}$ (10GBASE-SR over OM3), $400\,\text{m}$ (OM4) |
| **Typical Deployment** | Campus Backbone, Metro Ethernet, Long-Haul WAN | Data Center Intra-Rack / Top-of-Rack (ToR) Interconnect |

```
  SINGLE-MODE FIBER (SMF) - Single straight light ray path:
  Core (9µm)     ========================================> [Laser Light Ray]
  Cladding (125µm)

  MULTI-MODE FIBER (MMF) - Multiple bouncing light modes (Modal Dispersion):
  Core (50µm)    /\  /\  /\  /\  /\  /\  /\  /\  /\  /\  > [Mode 1]
                 \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  > [Mode 2]
  Cladding (125µm)
```

### 2.2 Optical Link Power Budget Calculation

An optical engineer must verify that the total channel attenuation does not exceed the optical transceiver power budget:

$$\text{Power Budget } (P_B) = P_{\text{TX,min}} - P_{\text{RX,sensitivity}} \quad [\text{dB}]$$

$$\text{Total Channel Loss } (L_{\text{total}}) = (\alpha \times D) + (N_{\text{splice}} \times L_{\text{splice}}) + (N_{\text{connector}} \times L_{\text{conn}}) + M_{\text{safety}}$$

- $\alpha$: Fiber attenuation coefficient (dB/km) (e.g., $0.35\,\text{dB/km}$ at $1310\,\text{nm}$, $0.22\,\text{dB/km}$ at $1550\,\text{nm}$)
- $D$: Link distance in km
- $L_{\text{splice}}$: Fusion splice insertion loss (typical $\le 0.05\,\text{dB}$)
- $L_{\text{conn}}$: LC/MPO connector loss (typical $0.25 - 0.5\,\text{dB}$)
- $M_{\text{safety}}$: Aging and repair safety margin (typically $3.0\,\text{dB}$)

**Requirement for Error-Free Transmission:**
$$P_B \ge L_{\text{total}} \quad \text{and} \quad P_{\text{TX,max}} - L_{\text{total}} \le P_{\text{RX,overload}}$$

---

## 3. Optical Transceiver Form Factors & Speed Matrix

```
+-------------------------------------------------------------------------------+
|                      TRANSCEIVER EVOLUTION MATRIX                             |
+-------------------------------------------------------------------------------+
| SFP       : 1 Gbps     | 1 electrical lane  @ 1.25 Gbps                      |
| SFP+      : 10 Gbps    | 1 electrical lane  @ 10.3125 Gbps (NRZ)              |
| SFP28     : 25 Gbps    | 1 electrical lane  @ 25.78125 Gbps (NRZ)             |
| QSFP+     : 40 Gbps    | 4 electrical lanes @ 10 Gbps (4x10G NRZ)             |
| QSFP28    : 100 Gbps   | 4 electrical lanes @ 25 Gbps (4x25G NRZ)             |
| QSFP-DD   : 400 Gbps   | 8 electrical lanes @ 50 Gbps (8x50G PAM4)            |
| OSFP      : 800 Gbps   | 8 electrical lanes @ 100 Gbps (8x100G PAM4)          |
+-------------------------------------------------------------------------------+
```

### 3.1 Transceiver Optical Standards & Reach

| Standard | Wavelength | Fiber Type | Max Distance | Connector | Modulation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **10GBASE-SR** | $850\,\text{nm}$ | MMF (OM3/OM4) | $300\,\text{m} / 400\,\text{m}$ | Duplex LC | NRZ |
| **10GBASE-LR** | $1310\,\text{nm}$ | SMF (OS2) | $10\,\text{km}$ | Duplex LC | NRZ |
| **25GBASE-SR** | $850\,\text{nm}$ | MMF (OM4) | $100\,\text{m}$ | Duplex LC | NRZ |
| **40GBASE-SR4** | $850\,\text{nm}$ | MMF (OM4) | $150\,\text{m}$ | MPO-12 | 4x NRZ |
| **100GBASE-SR4**| $850\,\text{nm}$ | MMF (OM4) | $100\,\text{m}$ | MPO-12 | 4x NRZ |
| **100GBASE-LR4**| $1295-1310\,\text{nm}$ | SMF (OS2) | $10\,\text{km}$ | Duplex LC (WDM) | 4x NRZ |
| **400GBASE-DR4**| $1310\,\text{nm}$ | SMF (OS2) | $500\,\text{m}$ | MPO-12 | 4x 100G PAM4 |
| **400GBASE-FR4**| CWDM4 (1271-1331) | SMF (OS2) | $2\,\text{km}$ | Duplex LC | CWDM PAM4 |

---

## 4. Copper Twisted Pair & Structured Cabling

### 4.1 TIA/EIA Category Specifications

```
+-----------------------------------------------------------------------------------+
| TIA/EIA Standards | Max Bandwidth | Max Ethernet Speed | Max Length | Shielding   |
+-----------------------------------------------------------------------------------+
| Cat5e             | 100 MHz       | 1000BASE-T (1 Gbps)| 100 m      | UTP         |
| Cat6              | 250 MHz       | 10GBASE-T (10 Gbps)| 55 m       | UTP / STP   |
| Cat6A             | 500 MHz       | 10GBASE-T (10 Gbps)| 100 m      | F/UTP, S/FTP|
| Cat7              | 600 MHz       | 10GBASE-T (10 Gbps)| 100 m      | S/FTP       |
| Cat8              | 2000 MHz      | 40GBASE-T (40 Gbps)| 30 m       | S/FTP       |
+-----------------------------------------------------------------------------------+
```

### 4.2 T568A vs. T568B Pinout Specification

```
  PIN  | T568A COLOR WIRE        | T568B COLOR WIRE
  -----+-------------------------+------------------------
   1   | White / Green           | White / Orange
   2   | Green                   | Orange
   3   | White / Orange          | White / Green
   4   | Blue                    | Blue
   5   | White / Blue            | White / Blue
   6   | Orange                  | Green
   7   | White / Brown           | White / Brown
   8   | Brown                   | Brown
```

---

## 5. Direct Attach Copper (DAC) vs. Active Optical Cable (AOC)

```
[ Top of Rack Switch (ToR) ]
     |                      |
  (DAC Passive Copper)   (Active Optical Cable AOC)
     |                      |
[ Server NIC 1 ]       [ Server NIC 2 ]
  - Distance: <= 3m      - Distance: up to 30m
  - Latency: < 10ns      - Latency: ~100ns (E/O conversion)
  - Power: ~0.1W/port    - Power: ~1.5W/port
```

---

## 6. CLI Diagnostics & Physical Layer Telemetry

### Cisco IOS-XE Optical DOM (Digital Optical Monitoring)

```bash
# Query transceiver optical power levels, voltage, temperature, and bias current
Switch# show interfaces GigabitEthernet0/1/0 transceiver detail

Transceiver Monitoring : Enabled
Internally calibrated  : Yes
Parameter         Value        High Alarm   Low Alarm    Status
----------------  -----------  -----------  -----------  --------
Temperature       34.2 C       75.0 C       -5.0 C       OK
Voltage           3.31 V       3.60 V       3.00 V       OK
Current (Bias)    22.4 mA      80.0 mA      2.0 mA       OK
Optical TX Power  -2.1 dBm     1.0 dBm      -10.0 dBm    OK
Optical RX Power  -4.8 dBm     -1.0 dBm     -18.0 dBm    OK
```

### Linux `ethtool` Physical Layer Query

```bash
# Query PHY link state, auto-negotiation, and supported speed capabilities
$ sudo ethtool eth0
Settings for eth0:
        Supported ports: [ FIBRE ]
        Supported link modes:   10000baseT/Full 25000baseCR/Full
        Speed: 25000Mb/s
        Duplex: Full
        Auto-negotiation: on
        Link detected: yes

# Query optical transceiver EEPROM registers (SFF-8472 DOM)
$ sudo ethtool -m eth0
        Receiver signal average optical power : 0.3340 mW (-4.76 dBm)
        Laser output power                    : 0.6120 mW (-2.13 dBm)
```
