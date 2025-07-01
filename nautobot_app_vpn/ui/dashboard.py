# === Production: nautobot_app_vpn/ui/dashboard.py ===
import logging
from django.views.generic import TemplateView
from nautobot.apps.views import NautobotUIViewSet
from nautobot_app_vpn.models import VPNDashboard

logger = logging.getLogger(__name__)


class VPNDashboardViewSet(NautobotUIViewSet):
    """
    Serves the new Cytoscape-based VPN dashboard.
    """

    queryset = VPNDashboard.objects.none()
    template_name = "nautobot_app_vpn/vpn_dashboard_cyto.html"

    def list(self, request, *args, **kwargs):
        return self.render_to_response({})
