"""Initialize the Nautobot VPN plugin API package."""

from .pagination import StandardResultsSetPagination
from .permissions import IsAdminOrReadOnly
from .serializers import (
    IKECryptoSerializer,
    IKEGatewaySerializer,
    IPSecCryptoSerializer,
    IPSECTunnelSerializer,
    TunnelMonitorProfileSerializer,
)
from .viewsets import (
    IKECryptoViewSet,
    IKEGatewayViewSet,
    IPSecCryptoViewSet,
    IPSECTunnelViewSet,
    TunnelMonitorProfileViewSet,
    VPNTopologyFilterOptionsView,
    VPNTopologyNeo4jView,
)

# Define what should be available when importing `api`
__all__ = [
    "StandardResultsSetPagination",
    "IsAdminOrReadOnly",
    "IKECryptoSerializer",
    "IPSecCryptoSerializer",
    "IKEGatewaySerializer",
    "IPSECTunnelSerializer",
    "TunnelMonitorProfileSerializer",
    "IKECryptoViewSet",
    "TunnelMonitorProfileViewSet",
    "IPSecCryptoViewSet",
    "IKEGatewayViewSet",
    "IPSECTunnelViewSet",
    "VPNTopologyNeo4jView",
    "VPNTopologyFilterOptionsView",
]

print("✅ Nautobot VPN: API Module Loaded Successfully")
