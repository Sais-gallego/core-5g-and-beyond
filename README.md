# Core 5G and Beyond (TKT21039)

[![5G Core CI](https://github.com/Sais-gallego/core-5g-and-beyond/actions/workflows/ci.yml/badge.svg)](https://github.com/Sais-gallego/core-5g-and-beyond/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)

Implementation of 3GPP Release 16/17 5G System Architecture, NG-RAN physical layer numerologies, Service-Based Architecture (SBA) Network Functions (AMF, SMF, UPF, AUSF, UDM, NRF), end-to-end Network Slicing (S-NSSAI, 5QI), and Multi-access Edge Computing (MEC) Uplink Classifier (UL CL) Local Breakout.

Developed for the **Core 5G and Beyond (TKT21039)** course at the **University of Helsinki**, Department of Computer Science.

---

## Architecture & Modules

```
core-5g-and-beyond/
├── src/
│   ├── service_based_architecture.py   # NRF (Nnrf_NFManagement, Nnrf_NFDiscovery)
│   ├── network_functions.py            # AMF, SMF, UPF (GTP-U), AUSF (5G-AKA), UDM
│   ├── network_slicing.py              # S-NSSAI, 5QI QoS profile lookup, admission control
│   ├── ran_simulator.py                # 5G NR numerology (mu=0..4), 3GPP TR 38.901 UMa-LOS, Shannon
│   ├── mec_edge_gateway.py             # ETSI MEC, Uplink Classifier (UL CL), Local Breakout (LBO)
│   └── __init__.py
├── tests/
│   ├── test_sba_and_nfs.py             # Unit tests for SBA, NRF, AMF, SMF, UPF, AUSF, UDM
│   ├── test_slicing_and_ran.py         # Unit tests for S-NSSAI, 5QI, NR numerology, path loss
│   └── test_mec_gateway.py             # Unit tests for MEC UL CL and latency reduction
├── SOLUTIONS.md                        # Theoretical guide & exam preparation
├── .github/workflows/ci.yml           # Multi-Python GitHub Actions pipeline
└── README.md
```

---

## Quick Start & Testing

Execute the test suite across all modules:

```bash
python -m unittest discover tests -v
```

All 17 tests validate 100% specification compliance with 3GPP TS 23.501, TS 23.502, TS 33.501, and TR 38.901.

---

## Author

**Sergio Andrés Ipuz Saavedra**  
Email: [afranklinromero@gmail.com](mailto:afranklinromero@gmail.com)  
GitHub: [@Sais-gallego](https://github.com/Sais-gallego)
