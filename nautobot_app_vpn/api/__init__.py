"""
Nautobot VPN Plugin API Initialization.
"""

# Import all API modules for easy reference
from .pagination import StandardResultsSetPagination
from .permissions import IsAdminOrReadOnly
from .serializers import IKECryptoSerializer, IPSecCryptoSerializer, IKEGatewaySerializer, IPSECTunnelSerializer, TunnelMonitorProfileSerializer
from .viewsets import IKECryptoViewSet, IPSecCryptoViewSet, IKEGatewayViewSet, IPSECTunnelViewSet,TunnelMonitorProfileViewSet, VPNTopologyNeo4jView, VPNTopologyFilterOptionsView

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
