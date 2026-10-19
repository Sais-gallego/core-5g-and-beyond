"""
5G Network Slicing & Quality of Service (QoS) Management.
3GPP TS 23.501 Section 5.15 & Section 5.7.
"""

from typing import Dict, List, Any, Optional


class StandardSliceType:
    """Standardized 3GPP Slice/Service Types (SST)."""
    EMBB = 1     # Enhanced Mobile Broadband
    URLLC = 2    # Ultra-Reliable Low-Latency Communication
    MIOT = 3     # Massive Internet of Things
    V2X = 4      # Vehicle-to-Everything


class QoSProfile:
    """3GPP 5QI (5G QoS Identifier) Profile characteristics."""

    CHARACTERISTICS = {
        1: {"type": "GBR", "packet_delay_budget_ms": 100, "packet_error_rate": 1e-2, "example": "Conversational Voice"},
        3: {"type": "GBR", "packet_delay_budget_ms": 50, "packet_error_rate": 1e-3, "example": "Real-Time Interactive Gaming"},
        9: {"type": "Non-GBR", "packet_delay_budget_ms": 300, "packet_error_rate": 1e-6, "example": "Default Internet Access"},
        82: {"type": "Delay-Critical GBR", "packet_delay_budget_ms": 10, "packet_error_rate": 1e-5, "example": "Industrial Discrete Automation"},
        85: {"type": "Delay-Critical GBR", "packet_delay_budget_ms": 5, "packet_error_rate": 1e-5, "example": "Autonomous V2X Platooning"}
    }

    @classmethod
    def get_profile(cls, qos_5qi: int) -> Dict[str, Any]:
        return cls.CHARACTERISTICS.get(qos_5qi, cls.CHARACTERISTICS[9])


class NetworkSlice:
    """Represents an instantiated virtual network slice identified by S-NSSAI."""

    def __init__(self, sst: int, sd: Optional[str] = None, guaranteed_mbps: float = 100.0, max_latency_ms: float = 50.0):
        self.sst = sst
        self.sd = sd or "000000"
        self.guaranteed_mbps = guaranteed_mbps
        self.max_latency_ms = max_latency_ms
        self.allocated_bandwidth_mbps = 0.0
        self.active_sessions: List[str] = []

    @property
    def snssai(self) -> str:
        return f"{self.sst}-{self.sd}"

    def can_admit_session(self, required_mbps: float, target_latency_ms: float) -> bool:
        if self.allocated_bandwidth_mbps + required_mbps > self.guaranteed_mbps:
            return False
        if target_latency_ms < self.max_latency_ms:
            return False
        return True

    def admit_session(self, session_id: str, required_mbps: float, target_latency_ms: float) -> bool:
        if not self.can_admit_session(required_mbps, target_latency_ms):
            return False
        self.allocated_bandwidth_mbps += required_mbps
        self.active_sessions.append(session_id)
        return True


class NetworkSliceManager:
    """Manages the creation, admission control, and lifecycle of 5G network slices."""

    def __init__(self):
        self.slices: Dict[str, NetworkSlice] = {}
        # Pre-provision default standardized slices
        self.create_slice(StandardSliceType.EMBB, "A1B2C3", guaranteed_mbps=1000.0, max_latency_ms=30.0)
        self.create_slice(StandardSliceType.URLLC, "000001", guaranteed_mbps=200.0, max_latency_ms=5.0)
        self.create_slice(StandardSliceType.MIOT, "000002", guaranteed_mbps=50.0, max_latency_ms=500.0)

    def create_slice(self, sst: int, sd: str, guaranteed_mbps: float, max_latency_ms: float) -> NetworkSlice:
        n_slice = NetworkSlice(sst, sd, guaranteed_mbps, max_latency_ms)
        self.slices[n_slice.snssai] = n_slice
        return n_slice

    def get_slice(self, sst: int, sd: str) -> Optional[NetworkSlice]:
        key = f"{sst}-{sd}"
        return self.slices.get(key)
