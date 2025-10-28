# nautobot_app_vpn/ui/dashboard.py
"""UI view definitions for the VPN plugin dashboard."""

import logging
from django.conf import settings
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.models import VPNDashboard

logger = logging.getLogger(__name__)


class VPNDashboardUIViewSet(NautobotUIViewSet):
    """Defines the dashboard tab for the VPN plugin.

    Switched to a MapLibre (OpenStreetMap) powered dashboard for accurate,
    interactive geo-visualization of VPN devices and tunnels. The previous
    Cytoscape-based view remains available as a template (vpn_dashboard_cyto.html)
    but is not used by default.
    """

    queryset = VPNDashboard.objects.none()
    template_name = "nautobot_app_vpn/vpn_dashboard_map.html"

    # Use a plain template renderer; no table expected
    renderer_classes = [TemplateHTMLRenderer]

    # Make it obvious this is not a tabular list view
    table_class = None
    filterset_class = None
    filterset_form_class = None
    action_buttons = ()

    def _map_context(self):
        map_cfg = (
            getattr(settings, "PLUGINS_CONFIG", {})
            .get("nautobot_app_vpn", {})
            .get("map", {})
        )

        return {
            # Back-compat (Leaflet-era keys)
            "MAP_TILES_URL": map_cfg.get(
                "tiles_url", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            ),
            "MAP_ATTRIBUTION": map_cfg.get(
                "attribution",
                "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
            ),
            "MAP_MAX_ZOOM": map_cfg.get("max_zoom", 19),
            # MapLibre
            "MAP_STYLE_URL": map_cfg.get(
                "style_url", "https://demotiles.maplibre.org/style.json"
            ),
            "MAP_INITIAL_LAT": map_cfg.get("initial_lat", 20),
            "MAP_INITIAL_LON": map_cfg.get("initial_lon", 0),
            "MAP_INITIAL_ZOOM": map_cfg.get("initial_zoom", 1.7),
            "MAP_INITIAL_PITCH": map_cfg.get("initial_pitch", 0),
            "MAP_INITIAL_BEARING": map_cfg.get("initial_bearing", 0),
        }

    def list(self, request, *args, **kwargs):
        # Render the template with map context; no table involved
        context = self._map_context()
        return Response(context, template_name=self.template_name)
