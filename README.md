# Nautobot VPN APP

&#x20;

A Nautobot plugin designed to model, visualize, and manage VPN infrastructure, including IPSec tunnels, IKE gateways, crypto profiles, and dynamic topology diagrams sourced from Neo4j.

---

## Key Features

- IKE Gateway and IPSec Tunnel modeling
- Inline or default crypto profile selection
- Dynamic tunnel provisioning form with interface auto-selection
- Topology visualization via Neo4j + Cytoscape


---

## Requirements

- Nautobot >= 2.2.0
- Python >= 3.8
- Neo4j >= 5.0 (for topology view)

---

## Installation

### 1. Install via pip

```bash
pip install nautobot-app-vpn
```

### 2. Enable the plugin

In your `nautobot_config.py`, add to `PLUGINS` and configure Neo4j settings:

```python
PLUGINS = [
    "nautobot_app_vpn",
    # ...
]

PLUGINS_CONFIG = {
    "nautobot_app_vpn": {
        "neo4j": {
            "uri": "bolt://neo4j:7687",
            "user": "neo4j",
            "password": "testneo4j",  # Change this
        }
    }
}
```

---

## Docker/Compose Setup (Optional)

If you are using `docker-compose`, include this plugin in your `plugin_requirements.txt`:

```text
nautobot-app-vpn
```

Then rebuild Nautobot:

```bash
docker-compose build nautobot
```

---

## Usage

### Topology View

The plugin provides a Neo4j-powered dashboard under **Plugins > VPN Dashboard**, enabling visualization of active IPSec tunnels and their metadata.

### Forms for Provisioning

- Auto-select interfaces based on ISP zone tags
- Auto-populate IPs from synced device data
- Support dynamic IP tunnels
- Create or select IKE/IPsec crypto profiles

---

## Screenshots

![VPN Menu](https://raw.githubusercontent.com/iss-world/nautobot-app-vpn/main/docs/images/image.png)

![VPN Dashboard](https://raw.githubusercontent.com/iss-world/nautobot-app-vpn/main/docs/images/image-1.png)

![IKE Crypto](https://raw.githubusercontent.com/iss-world/nautobot-app-vpn/main/docs/images/image-2.png)

![IPsec Crypto](https://raw.githubusercontent.com/iss-world/nautobot-app-vpn/main/docs/images/image-3.png)

![IKE Gateway](https://raw.githubusercontent.com/iss-world/nautobot-app-vpn/main/docs/images/image-4.png)

![IPSec Tunnel](https://raw.githubusercontent.com/iss-world/nautobot-app-vpn/main/docs/images/image-5.png)

![Tunnel Monitor](https://raw.githubusercontent.com/iss-world/nautobot-app-vpn/main/docs/images/image-6.png)

---

## Development

### Clone and install in editable mode:

```bash
git clone https://github.com/iss-world/nautobot-app-vpn.git
cd nautobot-app-vpn
poetry install
```

### Run linters locally

```bash
ruff check .
yamllint .
```

---

## Contributing

Pull requests are welcome! Please ensure code follows Nautobot plugin guidelines and passes all checks.

---

## License

Apache License 2.0. See [LICENSE](https://github.com/iss-world/nautobot-app-vpn/blob/main/LICENSE) for details.

---

## Author

Maintained by [@npolisetty26](https://github.com/npolisetty26)
