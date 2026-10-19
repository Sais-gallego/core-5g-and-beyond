"""
Unit tests for 5G Network Slicing and 5G NR Radio Propagation.
"""

import unittest
from src.network_slicing import StandardSliceType, QoSProfile, NetworkSlice, NetworkSliceManager
from src.ran_simulator import NrNumerology, RadioPropagationModel


class TestNetworkSlicing(unittest.TestCase):
    def setUp(self):
        self.mgr = NetworkSliceManager()

    def test_standard_slice_constants(self):
        self.assertEqual(StandardSliceType.EMBB, 1)
        self.assertEqual(StandardSliceType.URLLC, 2)
        self.assertEqual(StandardSliceType.MIOT, 3)
        self.assertEqual(StandardSliceType.V2X, 4)

    def test_qos_profile_lookup(self):
        prof_voice = QoSProfile.get_profile(1)
        self.assertEqual(prof_voice["type"], "GBR")
        self.assertEqual(prof_voice["packet_delay_budget_ms"], 100)

        prof_v2x = QoSProfile.get_profile(85)
        self.assertEqual(prof_v2x["type"], "Delay-Critical GBR")
        self.assertEqual(prof_v2x["packet_delay_budget_ms"], 5)

        prof_default = QoSProfile.get_profile(999)  # Fallback to 5QI 9
        self.assertEqual(prof_default["type"], "Non-GBR")
        self.assertEqual(prof_default["packet_delay_budget_ms"], 300)

    def test_slice_admission_control(self):
        embb_slice = self.mgr.get_slice(StandardSliceType.EMBB, "A1B2C3")
        self.assertIsNotNone(embb_slice)

        # Should admit valid session
        admitted = embb_slice.admit_session(session_id="sess-01", required_mbps=200.0, target_latency_ms=35.0)
        self.assertTrue(admitted)
        self.assertEqual(embb_slice.allocated_bandwidth_mbps, 200.0)

        # Should reject if latency budget is violated (requires <= 20 ms, but slice max is 30 ms)
        rejected_latency = embb_slice.admit_session(session_id="sess-02", required_mbps=50.0, target_latency_ms=20.0)
        self.assertFalse(rejected_latency)

        # Should reject if bandwidth limit exceeded (1000 Mbps capacity)
        rejected_bw = embb_slice.admit_session(session_id="sess-03", required_mbps=900.0, target_latency_ms=40.0)
        self.assertFalse(rejected_bw)


class TestRanSimulator(unittest.TestCase):
    def test_nr_numerologies(self):
        # mu = 0 (15 kHz SCS, sub-1GHz / LTE-compatible)
        p0 = NrNumerology.get_numerology_params(0)
        self.assertEqual(p0["subcarrier_spacing_khz"], 15)
        self.assertEqual(p0["slot_duration_ms"], 1.0)
        self.assertEqual(p0["slots_per_frame"], 10)

        # mu = 1 (30 kHz SCS, 3.5 GHz C-band)
        p1 = NrNumerology.get_numerology_params(1)
        self.assertEqual(p1["subcarrier_spacing_khz"], 30)
        self.assertEqual(p1["slot_duration_ms"], 0.5)
        self.assertEqual(p1["slots_per_frame"], 20)

        # mu = 3 (120 kHz SCS, mmWave 28 GHz)
        p3 = NrNumerology.get_numerology_params(3)
        self.assertEqual(p3["subcarrier_spacing_khz"], 120)
        self.assertEqual(p3["slot_duration_ms"], 0.125)
        self.assertEqual(p3["slots_per_frame"], 80)

        # Invalid mu
        with self.assertRaises(ValueError):
            NrNumerology.get_numerology_params(5)

    def test_urban_macro_los_path_loss(self):
        # 100 meters at 3.5 GHz
        pl_100m = RadioPropagationModel.urban_macro_los_path_loss_db(100.0, 3.5)
        self.assertGreater(pl_100m, 80.0)
        self.assertLess(pl_100m, 90.0)

        # Greater distance implies higher path loss
        pl_500m = RadioPropagationModel.urban_macro_los_path_loss_db(500.0, 3.5)
        self.assertGreater(pl_500m, pl_100m)

        # Edge cases
        self.assertEqual(RadioPropagationModel.urban_macro_los_path_loss_db(0, 3.5), 0.0)

    def test_shannon_channel_capacity(self):
        # 100 MHz bandwidth, 20 dB SINR
        cap = RadioPropagationModel.shannon_channel_capacity_mbps(100.0, 20.0)
        # C = 100 * log2(1 + 100) = 100 * 6.658 = ~665.8 Mbps
        self.assertGreater(cap, 660.0)
        self.assertLess(cap, 675.0)


if __name__ == "__main__":
    unittest.main()
