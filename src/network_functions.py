"""
5G Core Network Functions (AMF, SMF, UPF, AUSF, UDM).
3GPP TS 23.501 / TS 23.502 / TS 33.501.
"""

import hashlib
import hmac
import os
import uuid
from typing import Dict, Any, List, Optional, Tuple


class SubscriberDatabase:
    """Simulates UDM / UDR subscriber credential store."""

    def __init__(self):
        # Maps SUPI (e.g. imsi-244051234567890) -> {k: bytes, opc: bytes, allocated_ip: str}
        self.subscribers: Dict[str, Dict[str, Any]] = {}

    def add_subscriber(self, supi: str, key_hex: str, opc_hex: str):
        self.subscribers[supi] = {
            "k": bytes.fromhex(key_hex),
            "opc": bytes.fromhex(opc_hex),
            "allocated_ip": None,
            "subscribed_slices": [{"sst": 1, "sd": "A1B2C3"}, {"sst": 2, "sd": "000001"}]
        }


class UnifiedDataManagement:
    """Simulates 3GPP UDM for authentication credential handling and subscriber data."""

    def __init__(self, db: SubscriberDatabase):
        self.db = db

    def generate_auth_data(self, supi: str, sn_name: str) -> Dict[str, Any]:
        """
        Nudm_UEAuthentication_Get: Generates 5G-AKA authentication vector.
        Derives RAND, AUTN, XRES*, and K_ausf.
        """
        if supi not in self.db.subscribers:
            raise ValueError(f"Subscriber {supi} not found in UDM")

        k = self.db.subscribers[supi]["k"]
        rand = os.urandom(16)
        sqn = b"\x00\x00\x00\x00\x00\x01"

        # Milenage / HMAC-SHA256 simulation for 5G AKA
        mac = hmac.new(k, rand + sqn, hashlib.sha256).digest()[:8]
        autn = sqn + mac
        xres_star = hmac.new(k, rand + sn_name.encode(), hashlib.sha256).digest()[:16]
        k_ausf = hmac.new(k, b"5G_AUSF" + rand + sn_name.encode(), hashlib.sha256).digest()

        return {
            "rand": rand.hex(),
            "autn": autn.hex(),
            "xres_star": xres_star.hex(),
            "k_ausf": k_ausf.hex()
        }


class AuthenticationServerFunction:
    """Simulates 3GPP AUSF for UE mutual authentication."""

    def __init__(self, udm: UnifiedDataManagement):
        self.udm = udm

    def authenticate_ue(self, supi: str, sn_name: str = "5G:mnc005.mcc244.3gppnetwork.org") -> Dict[str, Any]:
        """Nausf_UEAuthentication_Authenticate operation."""
        auth_vector = self.udm.generate_auth_data(supi, sn_name)
        k_ausf = bytes.fromhex(auth_vector["k_ausf"])
        
        # Derive K_seaf for AMF
        k_seaf = hmac.new(k_ausf, b"5G_SEAF" + sn_name.encode(), hashlib.sha256).digest()
        return {
            "rand": auth_vector["rand"],
            "autn": auth_vector["autn"],
            "xres_star": auth_vector["xres_star"],
            "k_seaf": k_seaf.hex()
        }


class UserPlaneFunction:
    """Simulates 3GPP UPF for GTP-U encapsulation and packet routing."""

    def __init__(self, upf_id: str, ip_address: str = "10.0.0.1"):
        self.upf_id = upf_id
        self.ip_address = ip_address
        self.sessions: Dict[int, Dict[str, Any]] = {}  # teid -> session info
        self.next_teid = 1000

    def establish_n4_session(self, ue_ip: str, slice_info: Dict[str, Any], qos_5qi: int) -> int:
        """N4 Session Establishment (PFCP). Returns allocated GTP-U TEID."""
        teid = self.next_teid
        self.next_teid += 1
        self.sessions[teid] = {
            "ue_ip": ue_ip,
            "slice": slice_info,
            "5qi": qos_5qi,
            "packets_forwarded": 0,
            "bytes_forwarded": 0
        }
        return teid

    def forward_packet(self, teid: int, payload_bytes: int) -> bool:
        if teid in self.sessions:
            self.sessions[teid]["packets_forwarded"] += 1
            self.sessions[teid]["bytes_forwarded"] += payload_bytes
            return True
        return False


class SessionManagementFunction:
    """Simulates 3GPP SMF for PDU session creation, IP allocation, and UPF selection."""

    def __init__(self, smf_id: str, upf: UserPlaneFunction):
        self.smf_id = smf_id
        self.upf = upf
        self.pdu_sessions: Dict[str, Dict[str, Any]] = {}
        self.ip_pool = [f"10.45.0.{i}" for i in range(10, 250)]

    def establish_pdu_session(
        self,
        supi: str,
        pdu_session_id: int,
        dnn: str = "internet",
        slice_sst: int = 1,
        qos_5qi: int = 9
    ) -> Dict[str, Any]:
        """
        Nsmf_PDUSession_CreateSMContext.
        Allocates UE IP, contacts UPF over N4, and establishes user-plane path.
        """
        session_key = f"{supi}-{pdu_session_id}"
        if not self.ip_pool:
            raise RuntimeError("IP address pool exhausted")
        allocated_ip = self.ip_pool.pop(0)

        slice_info = {"sst": slice_sst}
        teid = self.upf.establish_n4_session(allocated_ip, slice_info, qos_5qi)

        session_record = {
            "supi": supi,
            "pduSessionId": pdu_session_id,
            "dnn": dnn,
            "allocatedIp": allocated_ip,
            "slice": slice_info,
            "5qi": qos_5qi,
            "upfTeid": teid,
            "status": "ESTABLISHED"
        }
        self.pdu_sessions[session_key] = session_record
        return session_record


class AccessAndMobilityManagementFunction:
    """
    Simulates 3GPP AMF for registration, authentication orchestration, and mobility management.
    """

    def __init__(self, amf_id: str, ausf: AuthenticationServerFunction, smf: SessionManagementFunction):
        self.amf_id = amf_id
        self.ausf = ausf
        self.smf = smf
        self.registered_ues: Dict[str, Dict[str, Any]] = {}

    def register_ue(self, supi: str, sn_name: str = "5G:mnc005.mcc244.3gppnetwork.org") -> Dict[str, Any]:
        """
        3GPP TS 23.502 Section 4.2.2.2 Registration Procedure.
        Orchestrates UE authentication with AUSF and allocates 5G-GUTI.
        """
        # 1. Authenticate with AUSF
        auth_resp = self.ausf.authenticate_ue(supi, sn_name)

        # 2. Allocate 5G Globally Unique Temporary Identifier (5G-GUTI)
        guti = f"5G-GUTI-{uuid.uuid4().hex[:12].upper()}"

        ue_context = {
            "supi": supi,
            "guti": guti,
            "state": "REGISTERED",
            "k_seaf": auth_resp["k_seaf"]
        }
        self.registered_ues[supi] = ue_context
        return ue_context
