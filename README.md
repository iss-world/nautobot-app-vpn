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

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

<p align="center">
  <img src="https://raw.githubusercontent.com/narendra.polisetty/nautobot-app-vpn/develop/docs/images/icon-nautobot_app_vpn.png" class="logo" height="200px">
  <br>
  <a href="https://git.noc.issworld.com/narendra.polisetty/nautobot-app-vpn/actions"><img src="https://git.noc.issworld.com/narendra.polisetty/nautobot-app-vpn/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/"><img src="https://readthedocs.org/projects/nautobot-app-nautobot-app-vpn/badge/"></a>
  <a href="https://pypi.org/project/nautobot_app_vpn/"><img src="https://img.shields.io/pypi/v/nautobot_app_vpn"></a>
  <a href="https://pypi.org/project/nautobot_app_vpn/"><img src="https://img.shields.io/pypi/dm/nautobot_app_vpn"></a>
  <br>
  An <a href="https://networktocode.com/nautobot-apps/">App</a> for <a href="https://nautobot.com/">Nautobot</a>.
</p>

## Overview

> Developer Note: Add a long (2-3 paragraphs) description of what the App does, what problems it solves, what functionality it adds to Nautobot, what external systems it works with etc.

### Screenshots

> Developer Note: Add any representative screenshots of the App in action. These images should also be added to the `docs/user/app_use_cases.md` section.

> Developer Note: Place the files in the `docs/images/` folder and link them using only full URLs from GitHub, for example: `![Overview](https://raw.githubusercontent.com/narendra.polisetty/nautobot-app-vpn/develop/docs/images/app-overview.png)`. This absolute static linking is required to ensure the README renders properly in GitHub, the docs site, and any other external sites like PyPI.

More screenshots can be found in the [Using the App](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/user/app_use_cases/) page in the documentation. Here's a quick overview of some of the app's added functionality:

![](https://raw.githubusercontent.com/narendra.polisetty/nautobot-app-vpn/develop/docs/images/placeholder.png)

## Try it out!

> Developer Note: Only keep this section if appropriate. Update link to correct sandbox.

This App is installed in the Nautobot Community Sandbox found over at [demo.nautobot.com](https://demo.nautobot.com/)!

> For a full list of all the available always-on sandbox environments, head over to the main page on [networktocode.com](https://www.networktocode.com/nautobot/sandbox-environments/).

## Documentation

Full documentation for this App can be found over on the [Nautobot Docs](https://docs.nautobot.com) website:

- [User Guide](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/user/app_overview/) - Overview, Using the App, Getting Started.
- [Administrator Guide](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/admin/install/) - How to Install, Configure, Upgrade, or Uninstall the App.
- [Developer Guide](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/dev/contributing/) - Extending the App, Code Reference, Contribution Guide.
- [Release Notes / Changelog](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/admin/release_notes/).
- [Frequently Asked Questions](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/user/faq/).

### Contributing to the Documentation

You can find all the Markdown source for the App documentation under the [`docs`](https://git.noc.issworld.com/narendra.polisetty/nautobot-app-vpn/tree/develop/docs) folder in this repository. For simple edits, a Markdown capable editor is sufficient: clone the repository and edit away.

If you need to view the fully-generated documentation site, you can build it with [MkDocs](https://www.mkdocs.org/). A container hosting the documentation can be started using the `invoke` commands (details in the [Development Environment Guide](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/dev/dev_environment/#docker-development-environment)) on [http://localhost:8001](http://localhost:8001). Using this container, as your changes to the documentation are saved, they will be automatically rebuilt and any pages currently being viewed will be reloaded in your browser.

Any PRs with fixes or improvements are very welcome!

## Questions

For any questions or comments, please check the [FAQ](https://docs.nautobot.com/projects/nautobot_app_vpn/en/latest/user/faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#nautobot`), sign up [here](http://slack.networktocode.com/) if you don't have an account.
