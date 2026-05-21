"""Read-only VPN adjacency contract helpers.

This module is intentionally defensive so that other plugins can rely on a
stable, JSON-safe contract without depending on Nautobot ORM internals.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
import ipaddress
from typing import Any, Iterable, Mapping

CONTRACT_VERSION = "1.0"
STATUS_NOT_EVALUATED = "not_evaluated"
STATUS_EMPTY = "empty"
STATUS_EVALUATED = "evaluated"
STATUS_AMBIGUOUS = "ambiguous"

WARNING_MULTIPLE_MATCHES = "multiple_vpn_adjacencies_matched"
WARNING_FRESHNESS_UNKNOWN = "vpn_freshness_unknown"
WARNING_RUNTIME_UNAVAILABLE = "vpn_runtime_unavailable"

FRESHNESS_FRESH = "fresh"
FRESHNESS_STALE = "stale"
FRESHNESS_UNKNOWN = "unknown"

DEFAULT_ENVIRONMENT = "production"
FRESHNESS_STALE_AFTER = timedelta(days=7)


class _UnavailableRuntime(RuntimeError):
    """Raised when Nautobot runtime is unavailable for ORM-backed evaluation."""


def vpn_adjacency_contract_version() -> str:
    """Return the stable VPN adjacency contract version string."""
    return CONTRACT_VERSION


def list_vpn_adjacencies(filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """List VPN adjacencies using the stable contract."""
    result = find_vpn_adjacencies(**dict(filters or {}))
    return list(result.get("adjacencies") or [])


def find_vpn_adjacencies(
    source: str | None = None,
    destination: str | None = None,
    device: str | None = None,
    site: str | None = None,
    environment: str = DEFAULT_ENVIRONMENT,
) -> dict[str, Any]:
    """Find VPN adjacencies that match a source/destination query."""
    query = {
        "source": source or "",
        "destination": destination or "",
        "device": device or "",
        "site": site or "",
        "environment": environment or DEFAULT_ENVIRONMENT,
    }
    result = _base_result(query)
    parsed_source = _parse_query_endpoint(source)
    parsed_destination = _parse_query_endpoint(destination)

    try:
        tunnels = list(_iter_tunnels(device=device, site=site))
    except _UnavailableRuntime as exc:
        result["warnings"].append(WARNING_RUNTIME_UNAVAILABLE)
        result["evidence"].append(_evidence("runtime", str(exc)))
        result["debug"]["runtime"] = "unavailable"
        return result
    except Exception as exc:  # pragma: no cover - defensive runtime fallback
        result["warnings"].append(WARNING_RUNTIME_UNAVAILABLE)
        result["evidence"].append(_evidence("runtime", "VPN runtime is available but adjacency evaluation failed."))
        result["debug"]["runtime_error"] = str(exc)
        return result

    if not tunnels:
        result["status"] = STATUS_EMPTY
        result["evidence"].append(_evidence("adjacency", "No VPN tunnel data is available for adjacency evaluation."))
        return result

    matched: list[dict[str, Any]] = []
    partial_matches: list[dict[str, Any]] = []
    warnings: set[str] = set()

    for tunnel in tunnels:
        adjacency = _build_adjacency(tunnel)
        match = _evaluate_match(adjacency, parsed_source, parsed_destination)
        adjacency["metadata"]["match"] = match

        if device and not _string_matches(device, adjacency.get("local_device"), adjacency.get("peer_device"), adjacency.get("peer_name")):
            continue
        if site and not _string_matches(site, adjacency.get("local_site"), adjacency.get("peer_site")):
            continue

        if adjacency.get("freshness") == FRESHNESS_UNKNOWN:
            warnings.add(WARNING_FRESHNESS_UNKNOWN)
        if match["include"]:
            if match["match_type"] == "partial":
                partial_matches.append(adjacency)
            else:
                matched.append(adjacency)

    chosen = matched or partial_matches
    result["adjacencies"] = chosen
    result["adjacency_count"] = len(chosen)
    result["warnings"] = sorted(warnings)

    if not chosen:
        result["status"] = STATUS_EVALUATED
        result["evidence"].append(_evidence("adjacency", "No matching VPN adjacency was found for the supplied query."))
        return result

    if len(chosen) > 1:
        result["status"] = STATUS_AMBIGUOUS
        result["warnings"] = sorted(set(result["warnings"]) | {WARNING_MULTIPLE_MATCHES})
        result["evidence"].append(_evidence("adjacency", "Multiple VPN adjacencies matched the supplied query."))
    else:
        result["status"] = STATUS_EVALUATED
        result["evidence"].append(_evidence("adjacency", "VPN adjacency evidence matched the supplied query."))

    return result


def _base_result(query: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": STATUS_NOT_EVALUATED,
        "contract_version": CONTRACT_VERSION,
        "query": _json_safe(dict(query)),
        "adjacency_count": 0,
        "adjacencies": [],
        "warnings": [],
        "evidence": [],
        "debug": {},
    }


def _runtime_available() -> bool:
    try:
        from django.apps import apps

        return apps.ready
    except Exception:
        return False


def _iter_tunnels(device: str | None = None, site: str | None = None) -> Iterable[Any]:
    if not _runtime_available():
        raise _UnavailableRuntime("Django/Nautobot runtime is not available for VPN adjacency evaluation.")

    from nautobot_app_vpn.models import IPSECTunnel

    queryset = (
        IPSECTunnel.objects.select_related("ike_gateway", "status", "tunnel_interface")
        .prefetch_related(
            "devices",
            "proxy_ids",
            "ike_gateway__local_devices",
            "ike_gateway__peer_devices",
            "ike_gateway__local_locations",
            "ike_gateway__peer_locations",
        )
        .order_by("name")
        .distinct()
    )
    return queryset


def _build_adjacency(tunnel: Any) -> dict[str, Any]:
    gateway = getattr(tunnel, "ike_gateway", None)
    local_devices = _many_to_list(getattr(gateway, "local_devices", None)) or _many_to_list(getattr(tunnel, "devices", None))
    peer_devices = _many_to_list(getattr(gateway, "peer_devices", None))
    local_locations = _many_to_list(getattr(gateway, "local_locations", None))
    peer_locations = _many_to_list(getattr(gateway, "peer_locations", None))
    proxy_ids = list(_many_to_list(getattr(tunnel, "proxy_ids", None)))

    local_proxy_ids = [_string_or_empty(getattr(item, "local_subnet", "")).strip() for item in proxy_ids if _string_or_empty(getattr(item, "local_subnet", "")).strip()]
    remote_proxy_ids = [_string_or_empty(getattr(item, "remote_subnet", "")).strip() for item in proxy_ids if _string_or_empty(getattr(item, "remote_subnet", "")).strip()]

    local_device = local_devices[0] if local_devices else None
    peer_device = peer_devices[0] if peer_devices else None
    local_location = local_locations[0] if local_locations else _object_location(local_device)
    peer_location = peer_locations[0] if peer_locations else _object_location(peer_device)
    bind_interface = getattr(gateway, "bind_interface", None)
    tunnel_interface = getattr(tunnel, "tunnel_interface", None)
    tunnel_status = getattr(getattr(tunnel, "status", None), "name", "") or "unknown"
    freshness = _freshness_for_tunnel(tunnel, gateway)

    metadata = {
        "direction": "unknown",
        "match_type": "none",
        "matched_proxy_ids": [],
        "local_device_names": [_display_name(item) for item in local_devices],
        "peer_device_names": [_display_name(item) for item in peer_devices],
        "local_location_names": [_display_name(item) for item in local_locations],
        "peer_location_names": [_display_name(item) for item in peer_locations],
        "gateway_last_sync": _isoformat(getattr(gateway, "last_sync", None)),
        "tunnel_last_sync": _isoformat(getattr(tunnel, "last_sync", None)),
    }

    adjacency = {
        "tunnel_name": _display_name(tunnel),
        "tunnel_id": _string_or_empty(getattr(tunnel, "pk", None)) or _string_or_empty(getattr(tunnel, "id", None)),
        "ike_gateway": _display_name(gateway),
        "local_device": _display_name(local_device),
        "local_device_id": _string_or_empty(getattr(local_device, "pk", None)) or _string_or_empty(getattr(local_device, "id", None)),
        "local_site": _display_name(local_location),
        "local_interface": _display_name(bind_interface),
        "tunnel_interface": _display_name(tunnel_interface),
        "peer_name": _peer_name(gateway, peer_device),
        "peer_device": _display_name(peer_device),
        "peer_device_id": _string_or_empty(getattr(peer_device, "pk", None)) or _string_or_empty(getattr(peer_device, "id", None)),
        "peer_site": _peer_site(gateway, peer_location),
        "peer_address": _string_or_empty(getattr(gateway, "peer_ip", "")),
        "local_proxy_ids": local_proxy_ids,
        "remote_proxy_ids": remote_proxy_ids,
        "local_interesting_traffic": list(local_proxy_ids),
        "remote_interesting_traffic": list(remote_proxy_ids),
        "status": tunnel_status,
        "freshness": freshness,
        "confidence": _confidence_for_adjacency(local_proxy_ids, remote_proxy_ids, local_device, peer_device),
        "source_system": "nautobot_app_vpn",
        "source_key": f"ipsectunnel:{_string_or_empty(getattr(tunnel, 'pk', None)) or _string_or_empty(getattr(tunnel, 'id', None))}",
        "metadata": _json_safe(metadata),
    }
    return _json_safe(adjacency)


def _evaluate_match(adjacency: Mapping[str, Any], parsed_source: Mapping[str, Any], parsed_destination: Mapping[str, Any]) -> dict[str, Any]:
    if not parsed_source["provided"] and not parsed_destination["provided"]:
        return {
            "include": True,
            "match_type": "list_all",
            "direction": "unknown",
            "matched_proxy_ids": [],
            "warnings": [],
        }

    matched_proxy_ids: list[dict[str, Any]] = []
    warnings: list[str] = []
    strong_match = False
    partial_match = False
    direction = "unknown"

    local_proxies = list(adjacency.get("local_proxy_ids") or [])
    remote_proxies = list(adjacency.get("remote_proxy_ids") or [])
    max_pairs = max(len(local_proxies), len(remote_proxies), 1)

    for index in range(max_pairs):
        local_proxy = local_proxies[index] if index < len(local_proxies) else ""
        remote_proxy = remote_proxies[index] if index < len(remote_proxies) else ""

        source_local = _match_endpoint(parsed_source, local_proxy)
        destination_remote = _match_endpoint(parsed_destination, remote_proxy)
        source_remote = _match_endpoint(parsed_source, remote_proxy)
        destination_local = _match_endpoint(parsed_destination, local_proxy)

        if source_local["matched"] and destination_remote["matched"]:
            strong_match = True
            direction = "local_to_remote"
            matched_proxy_ids.append({
                "local_proxy_id": local_proxy,
                "remote_proxy_id": remote_proxy,
                "direction": direction,
                "source_match": source_local["reason"],
                "destination_match": destination_remote["reason"],
            })
            continue
        if source_remote["matched"] and destination_local["matched"]:
            strong_match = True
            direction = "remote_to_local"
            matched_proxy_ids.append({
                "local_proxy_id": local_proxy,
                "remote_proxy_id": remote_proxy,
                "direction": direction,
                "source_match": source_remote["reason"],
                "destination_match": destination_local["reason"],
            })
            continue
        if source_local["matched"] or destination_remote["matched"] or source_remote["matched"] or destination_local["matched"]:
            partial_match = True
            matched_proxy_ids.append({
                "local_proxy_id": local_proxy,
                "remote_proxy_id": remote_proxy,
                "direction": "partial",
                "source_match": source_local["reason"] if source_local["matched"] else source_remote["reason"],
                "destination_match": destination_remote["reason"] if destination_remote["matched"] else destination_local["reason"],
            })

        for item in (source_local, destination_remote, source_remote, destination_local):
            if item.get("warning"):
                warnings.append(item["warning"])

    if strong_match:
        match_type = "full"
        include = True
    elif partial_match:
        match_type = "partial"
        include = True
    else:
        match_type = "none"
        include = False

    return {
        "include": include,
        "match_type": match_type,
        "direction": direction,
        "matched_proxy_ids": _json_safe(matched_proxy_ids),
        "warnings": sorted(set(warnings)),
    }


def _match_endpoint(endpoint: Mapping[str, Any], subnet_value: str) -> dict[str, Any]:
    if not endpoint["provided"]:
        return {"matched": True, "reason": "query_not_provided", "warning": ""}
    if endpoint["kind"] == "invalid":
        return {"matched": False, "reason": "invalid_query", "warning": "invalid_query_input"}

    normalized = _normalize_subnet_value(subnet_value)
    if normalized["kind"] == "wildcard":
        return {"matched": True, "reason": "wildcard_proxy", "warning": ""}
    if normalized["kind"] == "invalid":
        return {"matched": False, "reason": "invalid_proxy", "warning": "malformed_proxy_data"}

    if endpoint["family"] and normalized["family"] and endpoint["family"] != normalized["family"]:
        return {"matched": False, "reason": "address_family_mismatch", "warning": ""}

    if endpoint["kind"] == "ip":
        matched = endpoint["value"] in normalized["network"]
        return {"matched": matched, "reason": "ip_in_prefix" if matched else "ip_not_in_prefix", "warning": ""}

    endpoint_network = endpoint["value"]
    proxy_network = normalized["network"]
    matched = endpoint_network.subnet_of(proxy_network) or endpoint_network.supernet_of(proxy_network) or endpoint_network.overlaps(proxy_network)
    return {"matched": matched, "reason": "prefix_overlap" if matched else "prefix_no_overlap", "warning": ""}


def _parse_query_endpoint(value: str | None) -> dict[str, Any]:
    text = (value or "").strip()
    if not text:
        return {"provided": False, "kind": "", "value": None, "family": None}
    try:
        if "/" in text:
            network = ipaddress.ip_network(text, strict=False)
            return {"provided": True, "kind": "prefix", "value": network, "family": network.version}
        ip_value = ipaddress.ip_address(text)
        return {"provided": True, "kind": "ip", "value": ip_value, "family": ip_value.version}
    except ValueError:
        return {"provided": True, "kind": "invalid", "value": text, "family": None}


def _normalize_subnet_value(value: str | None) -> dict[str, Any]:
    text = (value or "").strip()
    if not text or text.lower() == "any":
        return {"kind": "wildcard", "network": None, "family": None}
    try:
        network = ipaddress.ip_network(text, strict=False)
        return {"kind": "network", "network": network, "family": network.version}
    except ValueError:
        return {"kind": "invalid", "network": None, "family": None}


def _peer_name(gateway: Any, peer_device: Any) -> str:
    manual = _string_or_empty(getattr(gateway, "peer_device_manual", "")).strip()
    if manual:
        return manual
    return _display_name(peer_device)


def _peer_site(gateway: Any, peer_location: Any) -> str:
    manual = _string_or_empty(getattr(gateway, "peer_location_manual", "")).strip()
    if manual:
        return manual
    return _display_name(peer_location)


def _confidence_for_adjacency(local_proxy_ids: list[str], remote_proxy_ids: list[str], local_device: Any, peer_device: Any) -> str:
    if local_proxy_ids and remote_proxy_ids and local_device and peer_device:
        return "high"
    if local_proxy_ids and remote_proxy_ids:
        return "medium"
    if local_proxy_ids or remote_proxy_ids:
        return "low"
    return "unknown"


def _freshness_for_tunnel(tunnel: Any, gateway: Any) -> str:
    timestamps = [getattr(tunnel, "last_sync", None), getattr(gateway, "last_sync", None)]
    usable = [item for item in timestamps if isinstance(item, datetime)]
    if not usable:
        return FRESHNESS_UNKNOWN
    latest = max(_coerce_datetime(item) for item in usable)
    now = datetime.now(timezone.utc)
    if now - latest <= FRESHNESS_STALE_AFTER:
        return FRESHNESS_FRESH
    return FRESHNESS_STALE


def _coerce_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _many_to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "all"):
        try:
            return list(value.all())
        except Exception:
            return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return []


def _object_location(obj: Any) -> Any:
    return getattr(obj, "location", None) if obj is not None else None


def _display_name(obj: Any) -> str:
    if obj is None:
        return ""
    for attr in ("name", "display", "label"):
        value = getattr(obj, attr, None)
        if value:
            return str(value)
    return str(obj)


def _isoformat(value: Any) -> str:
    if isinstance(value, datetime):
        return _coerce_datetime(value).isoformat()
    return ""


def _string_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


def _string_matches(value: str, *candidates: Any) -> bool:
    needle = value.strip().lower()
    if not needle:
        return True
    for candidate in candidates:
        text = _string_or_empty(candidate).strip().lower()
        if text and text == needle:
            return True
    return False


def _evidence(category: str, summary: str) -> dict[str, str]:
    return {"category": category, "summary": summary}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return _coerce_datetime(value).isoformat()
    if isinstance(value, ipaddress._BaseAddress):  # type: ignore[attr-defined]
        return str(value)
    if isinstance(value, ipaddress._BaseNetwork):  # type: ignore[attr-defined]
        return str(value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "pk") and hasattr(value, "name"):
        return {"id": _string_or_empty(getattr(value, "pk", None)), "name": _display_name(value)}
    return str(value)
