# Nautobot App VPN

A Nautobot plugin for visualizing VPN topologies using Neo4j and Cytoscape.js.

## 🔧 Features

- Neo4j-based dynamic VPN topology visualization
- Interactive dashboard powered by Cytoscape.js
- Flexible UI filters for location, device, platform, and more
- One-click export to PNG or JSON

> This plugin does **not** include Palo Alto-specific synchronization jobs. It is designed to be reusable and focused on topology visualization.

---

## 📦 Requirements

- Nautobot `>= 2.4.10`
- Python `>=3.11,<3.12`
- Neo4j `v5.x` running as a service

---

## 🚀 Installation

### 1. Install the plugin

```bash
pip install nautobot-app-vpn



### Add the plugin to your nautobot_config.py

# plugins
PLUGINS = ["nautobot_app_vpn"]

PLUGINS_CONFIG = {
    "nautobot_app_vpn": {}
}

# Neo4j connection (required for dashboard topology)
NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "testneo4j"

2. Run database migrations

nautobot-server migrate

3. Add Neo4j to Docker Compose
If you're running Nautobot via Docker Compose, add this service block:

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"   # Optional — browser access
      - "7687:7687"   # ✅ Required — Bolt protocol
    environment:
      NEO4J_AUTH: "neo4j/testneo4j"
    volumes:
      - ./neo4j_data:/data
    restart: unless-stopped


🧠 Usage
Navigate to VPN → VPN Dashboard in the Nautobot UI

Use filters to control visualization scope

Click Export PNG or Export JSON as needed

Ensure you have run the SyncNeo4jJob from Jobs → VPN → Sync Neo4j to populate the graph.

