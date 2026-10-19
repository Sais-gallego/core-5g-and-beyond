"""
5G New Radio (NR) Physical Layer Numerology & Propagation Simulator.
3GPP TS 38.211 / 3GPP TR 38.901.
"""

import math
from typing import Dict, Any, Tuple


class NrNumerology:
    """Computes 5G NR frame structure parameters for numerology index mu (0 to 4)."""

    @staticmethod
    def get_numerology_params(mu: int) -> Dict[str, Any]:
        if mu < 0 or mu > 4:
            raise ValueError("5G NR numerology mu must be an integer between 0 and 4")

        scs_khz = 15 * (2 ** mu)
        slot_duration_ms = 1.0 / (2 ** mu)
        slots_per_subframe = 2 ** mu
        slots_per_frame = 10 * (2 ** mu)
        symbols_per_slot = 14  # Normal Cyclic Prefix

        symbol_duration_us = (slot_duration_ms * 1000.0) / symbols_per_slot

        return {
            "mu": mu,
            "subcarrier_spacing_khz": scs_khz,
            "slot_duration_ms": slot_duration_ms,
            "slots_per_subframe": slots_per_subframe,
            "slots_per_frame": slots_per_frame,
            "symbols_per_slot": symbols_per_slot,
            "symbol_duration_us": round(symbol_duration_us, 3)
        }


class RadioPropagationModel:
    """Implements 3GPP TR 38.901 path loss formulas for sub-6 GHz and mmWave bands."""

    @staticmethod
    def urban_macro_los_path_loss_db(distance_3d_m: float, carrier_freq_ghz: float) -> float:
        """
        3GPP TR 38.901 Table 7.4.1-1 Urban Macro (UMa) Line-of-Sight (LOS) path loss:
        PL = 28.0 + 22.0 * log10(d_3D) + 20.0 * log10(f_c)
        Applicable for 10 m <= d_3D <= d_BP.
        """
        if distance_3d_m <= 0 or carrier_freq_ghz <= 0:
            return 0.0
        pl = 28.0 + 22.0 * math.log10(distance_3d_m) + 20.0 * math.log10(carrier_freq_ghz)
        return round(pl, 2)

    @staticmethod
    def shannon_channel_capacity_mbps(bandwidth_mhz: float, sinr_db: float) -> float:
        """
        Calculates theoretical peak channel capacity via Shannon-Hartley theorem:
        C = B * log2(1 + SINR_linear)
        """
        sinr_linear = 10.0 ** (sinr_db / 10.0)
        bandwidth_hz = bandwidth_mhz * 1e6
        capacity_bps = bandwidth_hz * math.log2(1.0 + sinr_linear)
        return round(capacity_bps / 1e6, 2)
