"""Form initializers for nautobot-app-vpn plugin."""

import logging

from nautobot_app_vpn.forms.ikecrypto import IKECryptoFilterForm, IKECryptoForm
from nautobot_app_vpn.forms.ikegateway import IKEGatewayFilterForm, IKEGatewayForm
from nautobot_app_vpn.forms.ipseccrypto import IPSecCryptoFilterForm, IPSecCryptoForm
from nautobot_app_vpn.forms.ipsectunnel import (
    IPSecProxyIDForm,
    IPSecProxyIDFormSet,
    IPSECTunnelFilterForm,
    IPSECTunnelForm,
)
from nautobot_app_vpn.forms.tunnelmonitor import TunnelMonitorProfileFilterForm, TunnelMonitorProfileForm

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
