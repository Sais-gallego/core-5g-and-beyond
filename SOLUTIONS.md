# Core 5G and Beyond (TKT21039) — Comprehensive Study Guide & Reference Solutions

**Course:** Core 5G and Beyond (TKT21039) — University of Helsinki, Faculty of Science, Department of Computer Science.  
**Student & Author:** Sergio Andrés Ipuz Saavedra (`@Sais-gallego`, `afranklinromero@gmail.com`)

---

## Executive Summary & Architecture Overview

The 5G System (5GS) standardized by 3GPP (Release 15 through 18) represents a revolutionary paradigm shift from legacy monolithic telecommunications architectures to cloud-native, microservice-driven, software-defined infrastructure.

Key architectural pillars of 5GS include:
1. **Control and User Plane Separation (CUPS):** Decoupling user plane packet forwarding (UPF) from control plane signaling (AMF, SMF, PCF), enabling independent elastic scaling and edge deployment.
2. **Service-Based Architecture (SBA):** Control Plane Network Functions (NFs) interact via uniform RESTful HTTP/2 APIs using JSON payloads and OpenAPI 3.0 definitions, discovered dynamically through the Network Repository Function (NRF).
3. **End-to-End Network Slicing:** Logical partitioning of physical compute, transport, and radio infrastructure into dedicated virtual networks identified by Single Network Slice Selection Assistance Information (S-NSSAI).
4. **Flexible Radio Access Network (NG-RAN):** Scalable numerology ($\mu \in \{0, 1, 2, 3, 4\}$), massive MIMO beamforming, dynamic TDD, and split RAN architectures (O-RAN CU-DU-RU).
5. **Multi-Access Edge Computing (MEC):** Uplink Classifier (UL CL) and Branching Point (BP) UPF mechanisms enabling low-latency Local Breakout (LBO) at the network perimeter.

---

## Chapter 1: 5G System Evolution & Architecture

### 1.1 Deployment Modes: Non-Standalone (NSA) vs. Standalone (SA)

3GPP defined multiple transition tracks from 4G LTE to 5G NR:
- **Option 3x (Non-Standalone - NSA):**
  - **Control Plane Anchor:** LTE eNodeB connected to the legacy Evolved Packet Core (EPC / MME).
  - **User Plane:** Traffic split between eNodeB and secondary 5G gNodeB (en-gNB).
  - **Advantage:** Rapid time-to-market using existing LTE EPC infrastructure.
  - **Limitation:** Lacks native SBA, true network slicing, and advanced 5G Core QoS controls.
- **Option 2 (Standalone - SA):**
  - **Control Plane & User Plane:** 5G gNodeB connected directly to the 5G Core (5GC) over N2 (NG-C) and N3 (NG-U) interfaces.
  - **Advantage:** Unlocks full 5GC capabilities: pure SBA, sub-millisecond URLLC, granular network slicing, native MEC.

```
       Option 3x (NSA)                      Option 2 (SA)
    +-------------------+               +-------------------+
    |    EPC (4G Core)  |               |    5GC (5G Core)  |
    |    (MME / S-GW)   |               |  (AMF, SMF, UPF)  |
    +---------+---------+               +---------+---------+
         S1-C |     \ S1-U                   N2-C |     \ N3-U
              |      \                            |      \
        +-----+--+  +-+------+              +-----+--+  +-+------+
        | LTE    |  | 5G     |              | 5G     |  | 5G     |
        | eNodeB |--| en-gNB |              | gNodeB |--| gNodeB |
        +--------+X2+--------+              +--------+Xn+--------+
```

### 1.2 Service-Based Architecture (SBA) Control Plane

In the 5G Core control plane, network functions act as Service Consumers and Service Producers across standardized service interfaces:

| NF Name | Functionality | Service Interface | Primary Service Operations |
|:---|:---|:---|:---|
| **NRF** | Network Repository Function | `Nnrf` | `NFRegister`, `NFUpdate`, `NFDeregister`, `NFDiscover` |
| **AMF** | Access & Mobility Management | `Namf` | `Communication`, `EventExposure`, `MT`, `Location` |
| **SMF** | Session Management Function | `Nsmf` | `PDUSession_CreateSMContext`, `PDUSession_UpdateSMContext` |
| **UDM** | Unified Data Management | `Nudm` | `UEAuthentication_Get`, `SubscriberDataManagement` |
| **AUSF** | Authentication Server Function | `Nausf` | `UEAuthentication_Authenticate` |
| **PCF** | Policy Control Function | `Npcf` | `SMPolicyControl`, `AMPolicyControl` |
| **NSSF** | Network Slice Selection Function| `Nnssf` | `NSSelection_Get` |
| **UPF** | User Plane Function | `N4` (PFCP) | Packet routing, encapsulation (GTP-U), policing, billing |

---

## Chapter 2: 5G Security, Identity & Authentication

### 2.1 Identity Privacy: SUPI vs. SUCI

In legacy 2G/3G/4G systems, the IMSI (International Mobile Subscriber Identity) was transmitted in cleartext over the radio link during initial attach, exposing subscribers to IMSI-catcher eavesdropping and tracking.

In 5G:
- **SUPI (Subscription Permanent Identifier):** The persistent subscriber identity (e.g., `imsi-244051234567890`), stored exclusively in the tamper-proof USIM and the operator's UDM/UDR.
- **SUCI (Subscription Concealed Identifier):** The encrypted identity generated on the USIM before over-the-air transmission.
  $$\text{SUCI} = \text{MCC} \,\|\, \text{MNC} \,\|\, \text{RoutingIndicator} \,\|\, \text{ProtectionScheme} \,\|\, \text{EphemeralPubKey} \,\|\, \text{Ciphertext} \,\|\, \text{MAC}$$
  Concealment uses ECIES (Elliptic Curve Integrated Encryption Scheme) with the Home Network Public Key stored on the SIM card. Only the Home UDM/SIDF (Subscription Identifier De-concealing Function) possesses the private key to decrypt the SUPI.

### 2.2 5G-AKA (Authentication and Key Agreement)

5G-AKA provides mutual authentication between the UE and the serving network, yielding cryptographic root keys:
1. **UE $\to$ AMF:** Registration request carrying SUCI.
2. **AMF $\to$ AUSF (`Nausf_UEAuthentication_Authenticate`):** Passes SUCI and Serving Network Name ($SN_{name}$).
3. **AUSF $\to$ UDM (`Nudm_UEAuthentication_Get`):** UDM verifies subscriber profile, executes Milenage algorithm with secret root key $K$:
   $$\text{RAND} \leftarrow \text{Random}(128\text{ bits})$$
   $$\text{AUTN} = (\text{SQN} \oplus \text{AK}) \,\|\, \text{AMF\_bits} \,\|\, \text{MAC}$$
   $$XRES^* = \text{KDF}(K, \text{RAND} \,\|\, SN_{name} \,\|\, \text{RES})$$
   $$K_{ausf} = \text{KDF}(K, \text{RAND} \,\|\, SN_{name} \,\|\, \text{SQN} \oplus \text{AK})$$
4. **AUSF Derivation:**
   $$K_{seaf} = \text{KDF}(K_{ausf}, SN_{name})$$
5. **AMF Derivation:**
   $$K_{amf} = \text{KDF}(K_{seaf}, \text{SUPI})$$
   $$\to K_{gNB} \text{ (for NG-RAN radio ciphering/integrity)}$$
   $$\to K_{nas\_enc}, K_{nas\_int} \text{ (for NAS signaling security)}$$

---

## Chapter 3: NG-RAN Physical Layer & Flexible Numerology

### 3.1 Scalable Subcarrier Spacing (SCS)

Unlike LTE with fixed $15\text{ kHz}$ subcarrier spacing and $1\text{ ms}$ subframe duration, 5G NR introduces scalable numerology parameter $\mu \in \{0, 1, 2, 3, 4\}$:

$$\Delta f = 15 \times 2^\mu \text{ [kHz]}$$
$$T_{slot} = \frac{1}{2^\mu} \text{ [ms]}$$

| $\mu$ | SCS ($\Delta f$) | Slot Duration | Slots / Subframe | Slots / Frame | Primary Frequency Band | Use Case |
|:---|:---|:---|:---|:---|:---|:---|
| **0** | $15\text{ kHz}$ | $1.0\text{ ms}$ | 1 | 10 | Sub-1 GHz (700 / 800 MHz) | Macro coverage, massive IoT |
| **1** | $30\text{ kHz}$ | $0.5\text{ ms}$ | 2 | 20 | Sub-6 GHz C-band (3.5 GHz) | Standard eMBB mobile capacity |
| **2** | $60\text{ kHz}$ | $0.25\text{ ms}$ | 4 | 40 | Sub-6 GHz / mmWave | Low-latency URLLC |
| **3** | $120\text{ kHz}$ | $0.125\text{ ms}$ | 8 | 80 | mmWave (26 / 28 / 39 GHz) | High throughput local hotspots |
| **4** | $240\text{ kHz}$ | $0.0625\text{ ms}$ | 16 | 160 | High mmWave (sync channels) | Specialized synchronization beams |

### 3.2 3GPP Propagation Models & Channel Capacity

3GPP TR 38.901 Urban Macro (UMa) Line-of-Sight (LOS) path loss model:
$$PL_{\text{UMa-LOS}} = 28.0 + 22.0 \log_{10}(d_{3D}) + 20.0 \log_{10}(f_c) \quad \text{[dB]}$$
where $d_{3D}$ is the 3D distance in meters and $f_c$ is carrier frequency in GHz.

Theoretical channel capacity is governed by the Shannon-Hartley theorem:
$$C = B \log_2\left(1 + \text{SINR}_{\text{linear}}\right) \quad \text{[bps]}$$

---

## Chapter 4: End-to-End Network Slicing & QoS Management

### 4.1 S-NSSAI Structure

A network slice is globally identified by **S-NSSAI** (Single Network Slice Selection Assistance Information):
$$\text{S-NSSAI} = \text{SST (8 bits)} + \text{SD (24 bits)}$$
- **SST (Slice/Service Type):**
  - `SST = 1`: Enhanced Mobile Broadband (eMBB)
  - `SST = 2`: Ultra-Reliable Low-Latency Communication (URLLC)
  - `SST = 3`: Massive Internet of Things (mIoT)
  - `SST = 4`: Vehicle-to-Everything (V2X)
- **SD (Slice Differentiator):** Optional 24-bit hexadecimal string distinguishing specific tenants, enterprise SLAs, or service providers.

### 4.2 5G QoS Flow Architecture (5QI)

5G replaces EPS bearers with fine-grained **QoS Flows**. All traffic mapping to the same QoS Flow receives identical packet forwarding treatment:
- **GBR (Guaranteed Bit Rate):** e.g., 5QI 1 (VoNR, PDB 100 ms, PER $10^{-2}$).
- **Non-GBR:** e.g., 5QI 9 (Default Internet, PDB 300 ms, PER $10^{-6}$).
- **Delay-Critical GBR:** e.g., 5QI 82 (Industrial automation, PDB 10 ms, PER $10^{-5}$), 5QI 85 (V2X platooning, PDB 5 ms, PER $10^{-5}$).

---

## Chapter 5: Multi-Access Edge Computing (MEC) & Local Breakout

In mission-critical URLLC and V2X use cases, sending traffic back to a centralized cloud data center introduces $30-80\text{ ms}$ round-trip transport latency.

MEC integrates directly into the 5G user plane via an **Uplink Classifier (UL CL)** running in an intermediate UPF (I-UPF):
1. **Traffic Inspection:** Evaluates packet headers (Destination IP prefix, UDP/TCP port, protocol).
2. **Local Breakout (LBO):** Diverts matching low-latency traffic locally over an N6-LAN interface to an on-premise Edge Application Server ($\approx 1-3\text{ ms}$ latency).
3. **Anchor Path:** Forwards normal non-latency-sensitive traffic along the N9 tunnel to the Central Anchor UPF and public cloud.

---

## Chapter 6: Verification & Test Execution

The codebase provides unit tests covering all mathematical models, protocols, and network functions:

```bash
python -m unittest discover tests -v
```

Output:
```
test_central_cloud_fallback (test_mec_gateway.TestMecEdgeGateway) ... ok
test_forwarding_statistics (test_mec_gateway.TestMecEdgeGateway) ... ok
test_local_breakout_routing (test_mec_gateway.TestMecEdgeGateway) ... ok
test_traffic_filter_matching (test_mec_gateway.TestMecEdgeGateway) ... ok
test_5g_aka_auth_vector_generation (test_sba_and_nfs.TestNetworkFunctions) ... ok
test_amf_registration_and_guti (test_sba_and_nfs.TestNetworkFunctions) ... ok
test_smf_pdu_session_establishment_and_upf_forwarding (test_sba_and_nfs.TestNetworkFunctions) ... ok
test_nf_deregistration (test_sba_and_nfs.TestServiceBasedArchitecture) ... ok
test_nf_discovery_and_load_balancing (test_sba_and_nfs.TestServiceBasedArchitecture) ... ok
test_nf_discovery_slice_filter (test_sba_and_nfs.TestServiceBasedArchitecture) ... ok
test_nf_registration_and_heartbeat (test_sba_and_nfs.TestServiceBasedArchitecture) ... ok
test_qos_profile_lookup (test_slicing_and_ran.TestNetworkSlicing) ... ok
test_slice_admission_control (test_slicing_and_ran.TestNetworkSlicing) ... ok
test_standard_slice_constants (test_slicing_and_ran.TestNetworkSlicing) ... ok
test_nr_numerologies (test_slicing_and_ran.TestRanSimulator) ... ok
test_shannon_channel_capacity (test_slicing_and_ran.TestRanSimulator) ... ok
test_urban_macro_los_path_loss (test_slicing_and_ran.TestRanSimulator) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.002s

OK
```
