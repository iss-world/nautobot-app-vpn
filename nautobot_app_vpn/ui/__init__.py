import logging

# Import all UI ViewSets for easy reference
from .dashboard import VPNDashboardViewSet
from .ikecrypto import IKECryptoUIViewSet
from .ikegateway import IKEGatewayUIViewSet
from .ipseccrypto import IPSecCryptoUIViewSet
from .ipsectunnel import IPSECTunnelUIViewSet
from .tunnelmonitor import TunnelMonitorProfileUIViewSet

# Define what should be available when importing `ui`
__all__ = [
    # ✅ UI ViewSets
    "VPNDashboardViewSet",
    "IKECryptoUIViewSet",
    "IKEGatewayUIViewSet",
    "IPSecCryptoUIViewSet",
    "IPSECTunnelUIViewSet",
    "TunnelMonitorProfileUIViewSet",
]

# 🚀 Logging for easier debugging
logger = logging.getLogger(__name__)
logger.info("✅ Nautobot VPN: UI ViewSets, Filters & Export Views Loaded Successfully")
