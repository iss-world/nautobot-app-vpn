from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "nautobot_app_vpn" / "services" / "adjacency.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("vpn_adjacency_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adjacency = _load_module()


class _Obj:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return getattr(self, "name", super().__str__())


class _Many:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)


class TestVpnAdjacencyService(unittest.TestCase):
    def _tunnel(
        self,
        *,
        local_subnets,
        remote_subnets,
        name="Tunnel-A",
        peer_name="peer-a",
        peer_ip="198.51.100.1",
        last_sync=None,
    ):
        now = datetime.now(timezone.utc)
        gateway = _Obj(
            name="gw-a",
            local_devices=_Many([_Obj(pk=11, name="fw-a", location=_Obj(name="DC1"))]),
            peer_devices=_Many([_Obj(pk=22, name="fw-b", location=_Obj(name="DC2"))]),
            local_locations=_Many([_Obj(name="DC1")]),
            peer_locations=_Many([_Obj(name="DC2")]),
            bind_interface=_Obj(name="ethernet1/1"),
            peer_device_manual=peer_name,
            peer_location_manual="",
            peer_ip=peer_ip,
            last_sync=last_sync,
        )
        proxies = []
        for local_subnet, remote_subnet in zip(local_subnets, remote_subnets):
            proxies.append(_Obj(local_subnet=local_subnet, remote_subnet=remote_subnet, protocol="any"))
        return _Obj(
            pk=101,
            id=101,
            name=name,
            ike_gateway=gateway,
            devices=_Many([_Obj(pk=11, name="fw-a", location=_Obj(name="DC1"))]),
            proxy_ids=_Many(proxies),
            tunnel_interface=_Obj(name="tunnel.100"),
            status=_Obj(name="active"),
            last_sync=last_sync or now,
        )

    def test_contract_version_exists(self):
        self.assertEqual(adjacency.vpn_adjacency_contract_version(), "1.0")

    def test_runtime_unavailable_returns_not_evaluated(self):
        with mock.patch.object(adjacency, "_iter_tunnels", side_effect=adjacency._UnavailableRuntime("no runtime")):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.1", destination="172.16.0.1")
        self.assertEqual(result["status"], adjacency.STATUS_NOT_EVALUATED)
        self.assertIn(adjacency.WARNING_RUNTIME_UNAVAILABLE, result["warnings"])

    def test_list_vpn_adjacencies_returns_stable_keys(self):
        tunnel = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"])
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            items = adjacency.list_vpn_adjacencies()
        self.assertEqual(len(items), 1)
        expected = {
            "tunnel_name",
            "tunnel_id",
            "ike_gateway",
            "local_device",
            "local_device_id",
            "local_site",
            "local_interface",
            "tunnel_interface",
            "peer_name",
            "peer_device",
            "peer_device_id",
            "peer_site",
            "peer_address",
            "local_proxy_ids",
            "remote_proxy_ids",
            "local_interesting_traffic",
            "remote_interesting_traffic",
            "status",
            "freshness",
            "confidence",
            "source_system",
            "source_key",
            "metadata",
        }
        self.assertTrue(expected.issubset(items[0].keys()))

    def test_find_handles_ip_input_local_to_remote(self):
        tunnel = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"])
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.1", destination="172.16.0.10")
        self.assertEqual(result["status"], adjacency.STATUS_EVALUATED)
        self.assertEqual(result["adjacency_count"], 1)
        self.assertEqual(result["adjacencies"][0]["metadata"]["match"]["direction"], "local_to_remote")

    def test_find_handles_prefix_input_remote_to_local(self):
        tunnel = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"])
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            result = adjacency.find_vpn_adjacencies(source="172.16.0.0/24", destination="10.0.0.0/24")
        self.assertEqual(result["status"], adjacency.STATUS_EVALUATED)
        self.assertEqual(result["adjacencies"][0]["metadata"]["match"]["direction"], "remote_to_local")

    def test_partial_match_is_retained(self):
        tunnel = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"])
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.1", destination="192.0.2.0/24")
        self.assertEqual(result["status"], adjacency.STATUS_EVALUATED)
        self.assertEqual(result["adjacencies"][0]["metadata"]["match"]["match_type"], "partial")

    def test_multiple_matches_produce_ambiguous_status(self):
        tunnel_a = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"], name="Tunnel-A")
        tunnel_b = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"], name="Tunnel-B")
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel_a, tunnel_b]):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.5", destination="172.16.0.9")
        self.assertEqual(result["status"], adjacency.STATUS_AMBIGUOUS)
        self.assertIn(adjacency.WARNING_MULTIPLE_MATCHES, result["warnings"])

    def test_malformed_proxy_data_does_not_crash(self):
        tunnel = self._tunnel(local_subnets=["not-a-prefix"], remote_subnets=["172.16.0.0/24"])
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.5", destination="172.16.0.9")
        self.assertIn(result["status"], {adjacency.STATUS_EVALUATED, adjacency.STATUS_EMPTY})
        self.assertIsInstance(result["adjacencies"], list)

    def test_ipv4_ipv6_mismatch_is_skipped_safely(self):
        tunnel = self._tunnel(local_subnets=["2001:db8::/64"], remote_subnets=["2001:db8:1::/64"])
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.5", destination="172.16.0.9")
        self.assertEqual(result["adjacency_count"], 0)

    def test_unknown_freshness_adds_warning(self):
        tunnel = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"], last_sync=None)
        tunnel.last_sync = None
        tunnel.ike_gateway.last_sync = None
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.1", destination="172.16.0.10")
        self.assertIn(adjacency.WARNING_FRESHNESS_UNKNOWN, result["warnings"])

    def test_stale_freshness_is_reported_on_adjacency(self):
        stale = datetime.now(timezone.utc) - timedelta(days=30)
        tunnel = self._tunnel(local_subnets=["10.0.0.0/24"], remote_subnets=["172.16.0.0/24"], last_sync=stale)
        with mock.patch.object(adjacency, "_iter_tunnels", return_value=[tunnel]):
            result = adjacency.find_vpn_adjacencies(source="10.0.0.1", destination="172.16.0.10")
        self.assertEqual(result["adjacencies"][0]["freshness"], adjacency.FRESHNESS_STALE)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
