"""
Unit tests for 5G SBA (NRF) and Network Functions (AMF, SMF, UPF, AUSF, UDM).
"""

import unittest
from src.service_based_architecture import NFProfile, NetworkRepositoryFunction
from src.network_functions import (
    SubscriberDatabase,
    UnifiedDataManagement,
    AuthenticationServerFunction,
    UserPlaneFunction,
    SessionManagementFunction,
    AccessAndMobilityManagementFunction,
)


class TestServiceBasedArchitecture(unittest.TestCase):
    def setUp(self):
        self.nrf = NetworkRepositoryFunction()
        self.amf_profile = NFProfile(
            nf_instance_id="amf-01",
            nf_type="AMF",
            ipv4_addresses=["10.100.0.1"],
            allowed_slices=[{"sst": 1, "sd": "A1B2C3"}],
            load=20
        )
        self.smf_profile_1 = NFProfile(
            nf_instance_id="smf-01",
            nf_type="SMF",
            ipv4_addresses=["10.100.0.2"],
            allowed_slices=[{"sst": 1, "sd": "A1B2C3"}],
            load=60
        )
        self.smf_profile_2 = NFProfile(
            nf_instance_id="smf-02",
            nf_type="SMF",
            ipv4_addresses=["10.100.0.3"],
            allowed_slices=[{"sst": 1, "sd": "A1B2C3"}, {"sst": 2, "sd": "000001"}],
            load=15
        )

    def test_nf_registration_and_heartbeat(self):
        res = self.nrf.register_nf(self.amf_profile)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("amf-01", self.nrf.registered_nfs)

        hb_res = self.nrf.update_heartbeat("amf-01")
        self.assertTrue(hb_res)

        hb_fail = self.nrf.update_heartbeat("non-existent")
        self.assertFalse(hb_fail)

    def test_nf_discovery_and_load_balancing(self):
        self.nrf.register_nf(self.smf_profile_1)
        self.nrf.register_nf(self.smf_profile_2)

        candidates = self.nrf.discover_nf(target_nf_type="SMF", requester_nf_type="AMF", slice_sst=1)
        self.assertEqual(len(candidates), 2)
        # Should be sorted by lowest load first: smf-02 (load 15) then smf-01 (load 60)
        self.assertEqual(candidates[0]["nfInstanceId"], "smf-02")
        self.assertEqual(candidates[1]["nfInstanceId"], "smf-01")

    def test_nf_discovery_slice_filter(self):
        self.nrf.register_nf(self.smf_profile_1)  # Only sst=1
        self.nrf.register_nf(self.smf_profile_2)  # sst=1 and sst=2

        candidates_urllc = self.nrf.discover_nf(target_nf_type="SMF", requester_nf_type="AMF", slice_sst=2)
        self.assertEqual(len(candidates_urllc), 1)
        self.assertEqual(candidates_urllc[0]["nfInstanceId"], "smf-02")

    def test_nf_deregistration(self):
        self.nrf.register_nf(self.amf_profile)
        self.assertTrue(self.nrf.deregister_nf("amf-01"))
        self.assertNotIn("amf-01", self.nrf.registered_nfs)
        self.assertFalse(self.nrf.deregister_nf("amf-01"))


class TestNetworkFunctions(unittest.TestCase):
    def setUp(self):
        self.db = SubscriberDatabase()
        self.supi = "imsi-244051234567890"
        self.key_hex = "00112233445566778899AABBCCDDEEFF"
        self.opc_hex = "FFEEDDCCBBAA99887766554433221100"
        self.db.add_subscriber(self.supi, self.key_hex, self.opc_hex)

        self.udm = UnifiedDataManagement(self.db)
        self.ausf = AuthenticationServerFunction(self.udm)
        self.upf = UserPlaneFunction(upf_id="upf-edge-01")
        self.smf = SessionManagementFunction(smf_id="smf-01", upf=self.upf)
        self.amf = AccessAndMobilityManagementFunction(amf_id="amf-01", ausf=self.ausf, smf=self.smf)

    def test_5g_aka_auth_vector_generation(self):
        auth_data = self.udm.generate_auth_data(self.supi, "5G:mnc005.mcc244.3gppnetwork.org")
        self.assertIn("rand", auth_data)
        self.assertIn("autn", auth_data)
        self.assertIn("xres_star", auth_data)
        self.assertIn("k_ausf", auth_data)

        # Invalid subscriber
        with self.assertRaises(ValueError):
            self.udm.generate_auth_data("imsi-unknown", "5G:mnc005.mcc244.3gppnetwork.org")

    def test_amf_registration_and_guti(self):
        ue_ctx = self.amf.register_ue(self.supi)
        self.assertEqual(ue_ctx["state"], "REGISTERED")
        self.assertTrue(ue_ctx["guti"].startswith("5G-GUTI-"))
        self.assertEqual(len(ue_ctx["k_seaf"]), 64)  # 32-byte hex

    def test_smf_pdu_session_establishment_and_upf_forwarding(self):
        session = self.smf.establish_pdu_session(
            supi=self.supi,
            pdu_session_id=1,
            dnn="internet",
            slice_sst=1,
            qos_5qi=9
        )
        self.assertEqual(session["status"], "ESTABLISHED")
        self.assertTrue(session["allocatedIp"].startswith("10.45.0."))
        teid = session["upfTeid"]
        self.assertGreaterEqual(teid, 1000)

        # Test forwarding packets through UPF
        success = self.upf.forward_packet(teid, 1500)
        self.assertTrue(success)
        self.assertEqual(self.upf.sessions[teid]["packets_forwarded"], 1)
        self.assertEqual(self.upf.sessions[teid]["bytes_forwarded"], 1500)

        # Invalid TEID forwarding
        fail = self.upf.forward_packet(99999, 1500)
        self.assertFalse(fail)


if __name__ == "__main__":
    unittest.main()
