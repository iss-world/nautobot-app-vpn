# VPN Adjacency API Contract

The VPN adjacency API provides a stable, read-only contract that other Nautobot apps can consume when they need VPN overlay evidence.

This API is designed for deterministic topology and troubleshooting workflows.
It is not routing truth, and it must not be used by itself to decide firewall, device-group, or security-zone placement.

## Why this API exists

The VPN app stores useful tunnel and proxy-ID context, but other apps should not need to understand the VPN plugin's internal model layout.
This contract exposes a normalized adjacency view that other plugins can consume safely.

## Core rules

- VPN adjacency is overlay evidence, not routing truth.
- Route and forwarding evidence must be evaluated separately.
- Tunnel match alone must not decide policy enforcement scope.
- The API is read-only.
- The API does not expose secrets such as pre-shared keys.

## Contract version

Use `contract_version` to detect future compatibility changes.

Current version:

```text
1.0
```

## Endpoint

```text
/api/plugins/nautobot_app_vpn/v1/vpn-adjacencies/
```

## Query parameters

- `source`
- `destination`
- `device`
- `site`
- `environment`

Notes:

- `source` and `destination` accept either an IP address or a prefix.
- `environment` defaults to `production`.
- `device` and `site` are optional narrowing filters.

## Top-level response shape

```json
{
  "status": "evaluated",
  "contract_version": "1.0",
  "query": {},
  "adjacency_count": 1,
  "adjacencies": [],
  "warnings": [],
  "evidence": [],
  "debug": {}
}
```

## Adjacency object shape

```json
{
  "tunnel_name": "Tunnel-A",
  "tunnel_id": "101",
  "ike_gateway": "gw-a",
  "local_device": "fw-a",
  "local_device_id": "11",
  "local_site": "DC1",
  "local_interface": "ethernet1/1",
  "tunnel_interface": "tunnel.100",
  "peer_name": "peer-a",
  "peer_device": "fw-b",
  "peer_device_id": "22",
  "peer_site": "DC2",
  "peer_address": "198.51.100.1",
  "local_proxy_ids": ["10.0.0.0/24"],
  "remote_proxy_ids": ["172.16.0.0/24"],
  "local_interesting_traffic": ["10.0.0.0/24"],
  "remote_interesting_traffic": ["172.16.0.0/24"],
  "status": "active",
  "freshness": "fresh",
  "confidence": "high",
  "source_system": "nautobot_app_vpn",
  "source_key": "ipsectunnel:101",
  "metadata": {}
}
```

## Matching behavior

The API evaluates `source` and `destination` against proxy-ID subnet pairs.

- If source matches local proxy traffic and destination matches remote proxy traffic, the match direction is `local_to_remote`.
- If source matches remote proxy traffic and destination matches local proxy traffic, the match direction is `remote_to_local`.
- If only one side matches, the tunnel is returned as a partial match.
- If neither side matches, the tunnel is not returned by lookup queries.
- Listing all adjacencies does not require a source or destination.

Direction and match details are placed in `metadata.match` so consumers can reason about them without depending on internal model fields.

## Status behavior

- `not_evaluated`: runtime is unavailable for ORM-backed evaluation
- `empty`: no VPN tunnel data is available
- `evaluated`: zero or more adjacencies were evaluated successfully
- `ambiguous`: more than one adjacency matched the query

## Freshness behavior

Freshness is derived conservatively from local `last_sync` timestamps.

- `fresh`
- `stale`
- `unknown`

Warnings may include:

- `multiple_vpn_adjacencies_matched`
- `vpn_freshness_unknown`
- `vpn_runtime_unavailable`

## Example lookup

```text
/api/plugins/nautobot_app_vpn/v1/vpn-adjacencies/?source=10.0.0.1&destination=172.16.0.0/24&environment=production
```

## How other plugins should consume this

Recommended use:

- consume the normalized response
- treat adjacency as overlay evidence only
- merge it with route, forwarding, and enforcement evidence
- surface warnings and freshness to operators

Not recommended:

- treating a VPN match as path truth
- directly importing or depending on VPN model internals in another plugin
- using VPN evidence by itself to auto-fill policy enforcement scope

## Limitations

- Proxy-ID data may be incomplete, wildcarded, or malformed.
- Tunnel freshness is only as good as the plugin's local sync timestamps.
- The API does not currently provide authoritative liveness validation.
- The API is intentionally read-only.

## Relationship to topology/path engines

This API is intended to support external topology engines such as Path Explorer.
Those consumers should layer VPN adjacency alongside:

- IPAM context
- RouteFact / ForwardingFact evidence
- enforcement evidence

VPN remains a supporting overlay signal, not the final path decision maker.
