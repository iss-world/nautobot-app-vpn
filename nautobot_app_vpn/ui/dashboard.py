"""UI view definitions for the VPN plugin dashboard."""

import logging

from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.models import VPNDashboard

logger = logging.getLogger(__name__)


class VPNDashboardUIViewSet(NautobotUIViewSet):
    """Defines the dashboard tab for the VPN plugin."""

    queryset = VPNDashboard.objects.none()
    template_name = "nautobot_app_vpn/vpn_dashboard_cyto.html"

    def list(self, request, *args, **kwargs):
        """Render the VPN dashboard template."""
        return self.render_to_response({})
