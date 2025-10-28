"""URL declarations for Nautobot VPN Plugin."""

import logging

from nautobot.apps.urls import NautobotUIViewSetRouter


from nautobot_app_vpn.ui.dashboard import VPNDashboardUIViewSet
from nautobot_app_vpn.ui.ikecrypto import IKECryptoUIViewSet
from nautobot_app_vpn.ui.ikegateway import IKEGatewayUIViewSet
from nautobot_app_vpn.ui.ipseccrypto import IPSecCryptoUIViewSet
from nautobot_app_vpn.ui.ipsectunnel import IPSECTunnelUIViewSet
from nautobot_app_vpn.ui.tunnelmonitor import TunnelMonitorProfileUIViewSet


logger = logging.getLogger(__name__)
app_name = "nautobot_app_vpn"

# --- Router for Standard Model Views ---
router = NautobotUIViewSetRouter()
router.register("ikecrypto", IKECryptoUIViewSet, basename="ikecrypto")
router.register("ikegateway", IKEGatewayUIViewSet, basename="ikegateway")
router.register("ipseccrypto", IPSecCryptoUIViewSet, basename="ipseccrypto")
router.register("ipsectunnel", IPSECTunnelUIViewSet, basename="ipsectunnel")
router.register("tunnel-monitor-profiles", TunnelMonitorProfileUIViewSet, basename="tunnelmonitorprofile")
router.register("dashboard", VPNDashboardUIViewSet, basename="vpn_dashboard")


urlpatterns = [
    *router.urls,
]

logger.info("✅ VPN Plugin URLs registered (Dashboard & Export paths added)")  # Updated log message
