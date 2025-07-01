import logging

from .ikecrypto import IKECryptoForm, IKECryptoFilterForm
from .ipseccrypto import IPSecCryptoForm, IPSecCryptoFilterForm
from .ikegateway import IKEGatewayForm, IKEGatewayFilterForm
from .ipsectunnel import IPSECTunnelForm, IPSecProxyIDForm, IPSecProxyIDFormSet, IPSECTunnelFilterForm
from .tunnelmonitor import TunnelMonitorProfileForm, TunnelMonitorProfileFilterForm

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
