"""Plugin navigation menu definition for Nautobot VPN app."""

from nautobot.core.apps import NavMenuGroup, NavMenuItem, NavMenuTab

menu_items = [
    NavMenuTab(
        name="VPN",
        weight=1000,
        groups=[
            NavMenuGroup(
                name="VPN Configuration",
                weight=100,
                items=[
                    NavMenuItem(
                        name="VPN Dashboard",
                        link="plugins:nautobot_app_vpn:vpn_dashboard_list",
                        weight=50,
                        permissions=["nautobot_app_vpn.view_vpndashboard"],
                    ),
                    NavMenuItem(
                        name="IKE Crypto Profiles",
                        link="plugins:nautobot_app_vpn:ikecrypto_list",
                        weight=100,
                        permissions=["nautobot_app_vpn.view_ikecrypto"],
                    ),
                    NavMenuItem(
                        name="IPSec Crypto Profiles",
                        link="plugins:nautobot_app_vpn:ipseccrypto_list",
                        weight=200,
                        permissions=["nautobot_app_vpn.view_ipseccrypto"],
                    ),
                    NavMenuItem(
                        name="Tunnel Monitor Profiles",
                        link="plugins:nautobot_app_vpn:tunnelmonitorprofile_list",
                        weight=250,
                        permissions=["nautobot_app_vpn.view_tunnelmonitorprofile"],
                    ),
                    NavMenuItem(
                        name="IKE Gateways",
                        link="plugins:nautobot_app_vpn:ikegateway_list",
                        weight=300,
                        permissions=["nautobot_app_vpn.view_ikegateway"],
                    ),
                    NavMenuItem(
                        name="IPSec Tunnels",
                        link="plugins:nautobot_app_vpn:ipsectunnel_list",
                        weight=400,
                        permissions=["nautobot_app_vpn.view_ipsectunnel"],
                    ),
                ],
            ),
            # Add other groups here if needed (e.g., for VPN Actions/Sync)
            # NavMenuGroup(
            #    name="VPN Actions",
            #    weight=200,
            #    items=[...]
            # ),
        ],
    ),
]
