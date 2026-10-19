"""
5G Core Service-Based Architecture (SBA) & Network Repository Function (NRF).
3GPP TS 23.501 / TS 29.510.
"""

from typing import Dict, List, Any, Optional
import time
import uuid


class NFProfile:
    """Represents an NF Profile registered in NRF according to 3GPP TS 29.510."""

    def __init__(
        self,
        nf_instance_id: str,
        nf_type: str,
        nf_status: str = "REGISTERED",
        ipv4_addresses: Optional[List[str]] = None,
        allowed_slices: Optional[List[Dict[str, Any]]] = None,
        capacity: int = 100,
        load: int = 0
    ):
        self.nf_instance_id = nf_instance_id
        self.nf_type = nf_type  # AMF, SMF, UPF, AUSF, UDM, PCF, NSSF
        self.nf_status = nf_status
        self.ipv4_addresses = ipv4_addresses or ["127.0.0.1"]
        self.allowed_slices = allowed_slices or []  # List of S-NSSAI {sst: int, sd: str}
        self.capacity = capacity
        self.load = load
        self.heartbeat_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nfInstanceId": self.nf_instance_id,
            "nfType": self.nf_type,
            "nfStatus": self.nf_status,
            "ipv4Addresses": self.ipv4_addresses,
            "allowedSlices": self.allowed_slices,
            "capacity": self.capacity,
            "load": self.load
        }


class NetworkRepositoryFunction:
    """
    Simulates the 3GPP NRF providing Nnrf_NFManagement and Nnrf_NFDiscovery services.
    Enables decentralized RESTful service discovery across 5G Core NFs.
    """

    def __init__(self):
        self.registered_nfs: Dict[str, NFProfile] = {}

    def register_nf(self, profile: NFProfile) -> Dict[str, Any]:
        """Nnrf_NFManagement_NFRegister service operation."""
        self.registered_nfs[profile.nf_instance_id] = profile
        return {"status": "SUCCESS", "nfProfile": profile.to_dict()}

    def deregister_nf(self, nf_instance_id: str) -> bool:
        """Nnrf_NFManagement_NFDeregister service operation."""
        if nf_instance_id in self.registered_nfs:
            del self.registered_nfs[nf_instance_id]
            return True
        return False

    def update_heartbeat(self, nf_instance_id: str) -> bool:
        """Nnrf_NFManagement_NFStatusUpdate operation."""
        if nf_instance_id in self.registered_nfs:
            self.registered_nfs[nf_instance_id].heartbeat_time = time.time()
            return True
        return False

    def discover_nf(
        self,
        target_nf_type: str,
        requester_nf_type: str,
        slice_sst: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Nnrf_NFDiscovery_Request service operation.
        Discovers active candidate NFs based on target type and optional network slice.
        """
        candidates = []
        for nf in self.registered_nfs.values():
            if nf.nf_type == target_nf_type and nf.nf_status == "REGISTERED":
                if slice_sst is not None:
                    # Check if NF supports requested slice SST
                    matched_slice = any(s.get("sst") == slice_sst for s in nf.allowed_slices)
                    if not matched_slice:
                        continue
                candidates.append(nf.to_dict())

        # Sort candidates by lowest load
        candidates.sort(key=lambda c: c.get("load", 0))
        return candidates
