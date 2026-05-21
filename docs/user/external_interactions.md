# External Interactions

This document describes external dependencies and prerequisites for this App to operate, including system requirements, API endpoints, interconnection or integrations to other applications or services, and similar topics.

!!! warning "Developer Note - Remove Me!"
    Optional page, remove if not applicable.

## External System Integrations

### From the App to Other Systems

### From Other Systems to the App

## Nautobot REST API endpoints

### VPN adjacency API

The VPN plugin exposes a read-only VPN adjacency contract for other Nautobot apps and troubleshooting tools:

```text
/api/plugins/nautobot_app_vpn/v1/vpn-adjacencies/
```

See [VPN Adjacency API Contract](vpn_adjacency_api.md) for the normalized response format, matching behavior, and limitations.
