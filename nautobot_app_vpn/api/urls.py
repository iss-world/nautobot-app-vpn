"""API URL declarations for the Nautobot VPN app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from nautobot_app_vpn.api.viewsets import (
    IKECryptoViewSet,
    IKEGatewayViewSet,
    IPSecCryptoViewSet,
    IPSecProxyIDViewSet,
    IPSECTunnelViewSet,
    TunnelMonitorProfileViewSet,
    VPNTopologyFilterOptionsView,
    VPNTopologyNeo4jView,
)

app_name = "nautobot_app_vpn_api"

# Register your API routes here
router = DefaultRouter()
router.register(r"ikecrypto", IKECryptoViewSet, basename="ikecrypto")
router.register(r"ipseccrypto", IPSecCryptoViewSet, basename="ipseccrypto")
router.register(r"ikegateway", IKEGatewayViewSet, basename="ikegateway")
router.register(r"ipsectunnel", IPSECTunnelViewSet, basename="ipsectunnel")
router.register(r"ipsecproxyid", IPSecProxyIDViewSet, basename="ipsecproxyid")
router.register(r"tunnel-monitor-profiles", TunnelMonitorProfileViewSet, basename="tunnelmonitorprofile")

urlpatterns = [
    path("v1/", include(router.urls)),  # ✅ Current versioned API path
    path("v1/topology-neo4j/", VPNTopologyNeo4jView.as_view(), name="vpn-topology-neo4j"),
    path("v1/topology-filters/", VPNTopologyFilterOptionsView.as_view(), name="vpn-topology-filters"),
]
