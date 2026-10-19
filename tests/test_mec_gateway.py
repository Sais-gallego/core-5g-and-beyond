"""
Unit tests for Multi-access Edge Computing (MEC) and Uplink Classifier (UL CL).
"""

import unittest
from src.mec_edge_gateway import (
    TrafficFilter,
    EdgeApplicationServer,
    CentralCloudServer,
    MecEdgeGateway,
)


class TestMecEdgeGateway(unittest.TestCase):
    def setUp(self):
        self.central_cloud = CentralCloudServer(cloud_ip="198.51.100.1", rtt_latency_ms=50.0)
        self.gateway = MecEdgeGateway(self.central_cloud)

        self.edge_v2x = EdgeApplicationServer(service_id="v2x-platoon-service", edge_ip="10.0.1.5", processing_delay_ms=2.0)
        filter_v2x = TrafficFilter(dest_ip_prefix="10.0.1.", dest_port=8080, protocol="UDP")
        self.gateway.register_edge_service(filter_v2x, self.edge_v2x)

        self.edge_video = EdgeApplicationServer(service_id="edge-ar-vr-service", edge_ip="10.0.2.10", processing_delay_ms=4.0)
        filter_video = TrafficFilter(dest_ip_prefix="10.0.2.", dest_port=9000, protocol="TCP")
        self.gateway.register_edge_service(filter_video, self.edge_video)

    def test_traffic_filter_matching(self):
        tf = TrafficFilter(dest_ip_prefix="10.0.1.", dest_port=8080, protocol="UDP")
        self.assertTrue(tf.matches({"dest_ip": "10.0.1.5", "dest_port": 8080, "protocol": "udp"}))
        self.assertFalse(tf.matches({"dest_ip": "10.0.2.5", "dest_port": 8080, "protocol": "UDP"}))
        self.assertFalse(tf.matches({"dest_ip": "10.0.1.5", "dest_port": 80, "protocol": "UDP"}))
        self.assertFalse(tf.matches({"dest_ip": "10.0.1.5", "dest_port": 8080, "protocol": "TCP"}))

    def test_local_breakout_routing(self):
        # Packet targeting edge V2X
        packet_v2x = {
            "dest_ip": "10.0.1.5",
            "dest_port": 8080,
            "protocol": "UDP",
            "payload": "telemetry_data"
        }
        res_v2x = self.gateway.route_uplink_packet(packet_v2x)
        self.assertEqual(res_v2x["route"], "LOCAL_BREAKOUT")
        self.assertEqual(res_v2x["service_id"], "v2x-platoon-service")
        self.assertEqual(res_v2x["edge_latency_ms"], 2.0)
        self.assertEqual(self.edge_v2x.processed_requests, 1)

    def test_central_cloud_fallback(self):
        # Packet targeting remote public internet
        packet_internet = {
            "dest_ip": "8.8.8.8",
            "dest_port": 53,
            "protocol": "UDP",
            "payload": "dns_query"
        }
        res_cloud = self.gateway.route_uplink_packet(packet_internet)
        self.assertEqual(res_cloud["route"], "CENTRAL_CLOUD")
        self.assertEqual(res_cloud["cloud_latency_ms"], 50.0)
        self.assertEqual(self.central_cloud.processed_requests, 1)

    def test_forwarding_statistics(self):
        self.gateway.route_uplink_packet({"dest_ip": "10.0.1.5", "dest_port": 8080, "protocol": "UDP", "payload": "1"})
        self.gateway.route_uplink_packet({"dest_ip": "10.0.1.5", "dest_port": 8080, "protocol": "UDP", "payload": "2"})
        self.gateway.route_uplink_packet({"dest_ip": "1.1.1.1", "dest_port": 80, "protocol": "TCP", "payload": "3"})

        stats = self.gateway.forwarding_stats
        self.assertEqual(stats["local_breakout_count"], 2)
        self.assertEqual(stats["central_cloud_count"], 1)


if __name__ == "__main__":
    unittest.main()
