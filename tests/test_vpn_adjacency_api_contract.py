from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class TestVpnAdjacencyApiContract(unittest.TestCase):
    def test_service_module_exists(self):
        path = REPO_ROOT / "nautobot_app_vpn" / "services" / "adjacency.py"
        self.assertTrue(path.exists())

    def test_viewset_defines_vpn_adjacency_view(self):
        content = (REPO_ROOT / "nautobot_app_vpn" / "api" / "viewsets.py").read_text()
        self.assertIn("class VPNAdjacencyView(APIView)", content)
        self.assertIn("find_vpn_adjacencies(", content)

    def test_api_urls_expose_vpn_adjacencies_route(self):
        content = (REPO_ROOT / "nautobot_app_vpn" / "api" / "urls.py").read_text()
        self.assertIn('path("v1/vpn-adjacencies/", VPNAdjacencyView.as_view(), name="vpn-adjacencies")', content)

    def test_serializer_exposes_expected_fields(self):
        content = (REPO_ROOT / "nautobot_app_vpn" / "api" / "serializers.py").read_text()
        self.assertIn("class VPNAdjacencySerializer(serializers.Serializer)", content)
        self.assertIn("class VPNAdjacencyLookupSerializer(serializers.Serializer)", content)
        for field_name in [
            "tunnel_name",
            "tunnel_id",
            "local_device",
            "peer_device",
            "local_proxy_ids",
            "remote_proxy_ids",
            "freshness",
            "confidence",
            "adjacency_count",
            "adjacencies",
            "warnings",
        ]:
            self.assertIn(field_name, content)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
