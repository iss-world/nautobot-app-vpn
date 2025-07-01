import logging

from .ikecrypto import IKECryptoFilterForm, IKECryptoForm
from .ikegateway import IKEGatewayFilterForm, IKEGatewayForm
from .ipseccrypto import IPSecCryptoFilterForm, IPSecCryptoForm
from .ipsectunnel import IPSecProxyIDForm, IPSecProxyIDFormSet, IPSECTunnelFilterForm, IPSECTunnelForm
from .tunnelmonitor import TunnelMonitorProfileFilterForm, TunnelMonitorProfileForm

logger = logging.getLogger(__name__)

__all__ = [
    "IKECryptoForm",
    "IKECryptoFilterForm",
    "IPSecCryptoForm",
    "IPSecCryptoFilterForm",
    "IKEGatewayForm",
    "IKEGatewayFilterForm",
    "IPSECTunnelForm",
    "IPSecProxyIDForm",
    "IPSecProxyIDFormSet",
    "IPSECTunnelFilterForm",
    "TunnelMonitorProfileForm",
    "TunnelMonitorProfileFilterForm",
]

logger.debug("✅ Nautobot VPN: Forms module loaded successfully")
