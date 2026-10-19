"""
Multi-access Edge Computing (MEC) & Uplink Classifier (UL CL) Local Breakout.
ETSI GS MEC 003 / 3GPP TS 23.501 Section 5.6.7.
"""

from typing import Dict, List, Any, Optional
import time


class TrafficFilter:
    """Defines a packet detection rule (PDR) for uplink traffic classification."""

    def __init__(self, dest_ip_prefix: str, dest_port: Optional[int] = None, protocol: str = "UDP"):
        self.dest_ip_prefix = dest_ip_prefix
        self.dest_port = dest_port
        self.protocol = protocol.upper()

    def matches(self, packet: Dict[str, Any]) -> bool:
        """Evaluates whether packet satisfies filter criteria."""
        dst_ip = packet.get("dest_ip", "")
        dst_port = packet.get("dest_port")
        proto = packet.get("protocol", "UDP").upper()

        if not dst_ip.startswith(self.dest_ip_prefix):
            return False
        if self.dest_port is not None and dst_port != self.dest_port:
            return False
        if self.protocol != proto:
            return False
        return True


class EdgeApplicationServer:
    """Simulates an ETSI MEC edge host running low-latency microservices."""

    def __init__(self, service_id: str, edge_ip: str, processing_delay_ms: float = 1.5):
        self.service_id = service_id
        self.edge_ip = edge_ip
        self.processing_delay_ms = processing_delay_ms
        self.processed_requests: int = 0

    def process_workload(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        self.processed_requests += 1
        return {
            "status": "PROCESSED_AT_EDGE",
            "service_id": self.service_id,
            "edge_ip": self.edge_ip,
            "edge_latency_ms": self.processing_delay_ms,
            "data_len": len(str(packet.get("payload", "")))
        }


class CentralCloudServer:
    """Simulates a remote central cloud application server."""

    def __init__(self, cloud_ip: str = "198.51.100.1", rtt_latency_ms: float = 45.0):
        self.cloud_ip = cloud_ip
        self.rtt_latency_ms = rtt_latency_ms
        self.processed_requests: int = 0

    def process_workload(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        self.processed_requests += 1
        return {
            "status": "PROCESSED_AT_CENTRAL_CLOUD",
            "cloud_ip": self.cloud_ip,
            "cloud_latency_ms": self.rtt_latency_ms,
            "data_len": len(str(packet.get("payload", "")))
        }


class MecEdgeGateway:
    """
    3GPP Uplink Classifier (UL CL) & MEC Local Breakout (LBO) router.
    Inspects user-plane packets: directs low-latency MEC traffic to the edge host,
    and forwards regular traffic through the central UPF anchor.
    """

    def __init__(self, central_cloud: Optional[CentralCloudServer] = None):
        self.central_cloud = central_cloud or CentralCloudServer()
        self.edge_services: Dict[str, EdgeApplicationServer] = {}
        self.ul_cl_rules: List[Dict[str, Any]] = []
        self.forwarding_stats = {
            "local_breakout_count": 0,
            "central_cloud_count": 0
        }

    def register_edge_service(
        self,
        traffic_filter: TrafficFilter,
        edge_app: EdgeApplicationServer
    ):
        """Associates a traffic filter with a local MEC edge service."""
        self.edge_services[edge_app.service_id] = edge_app
        self.ul_cl_rules.append({
            "filter": traffic_filter,
            "service_id": edge_app.service_id
        })

    def route_uplink_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies UL CL packet detection rules.
        If matched, delivers packet via Local Breakout (LBO).
        Otherwise, routes to the central cloud.
        """
        for rule in self.ul_cl_rules:
            traffic_filter: TrafficFilter = rule["filter"]
            if traffic_filter.matches(packet):
                service_id = rule["service_id"]
                edge_app = self.edge_services[service_id]
                self.forwarding_stats["local_breakout_count"] += 1
                res = edge_app.process_workload(packet)
                res["route"] = "LOCAL_BREAKOUT"
                return res

        # Default route to Central Cloud Anchor
        self.forwarding_stats["central_cloud_count"] += 1
        res = self.central_cloud.process_workload(packet)
        res["route"] = "CENTRAL_CLOUD"
        return res
