"""Initialize Nautobot VPN plugin models package."""

import logging

from .constants import (
    AuthenticationAlgorithms,
    DiffieHellmanGroups,
    EncryptionAlgorithms,
    IdentificationTypes,
    IKEAuthenticationTypes,
    IKEExchangeModes,
    IKEVersions,
    IPAddressTypes,
    IPSECProtocols,
    LifetimeUnits,
)
from .ikecrypto import IKECrypto
from .ikegateway import IKEGateway
from .ipseccrypto import IPSecCrypto
from .ipsectunnel import IPSecProxyID, IPSECTunnel, TunnelRoleChoices
from .tunnelmonitor import TunnelMonitorActionChoices, TunnelMonitorProfile
from .vpn_dashboard import VPNDashboard

# ✅ Logger for better debugging
logger = logging.getLogger(__name__)

__all__ = [
    "IKECrypto",
    "IKEGateway",
    "IPSecCrypto",
    "IPSECTunnel",
    "IPSecProxyID",
    "TunnelRoleChoices",
    "VPNDashboard",
    "TunnelMonitorProfile",
    "EncryptionAlgorithms",
    "AuthenticationAlgorithms",
    "DiffieHellmanGroups",
    "IKEAuthenticationTypes",
    "IPSECProtocols",
    "LifetimeUnits",
    "IKEVersions",
    "IKEExchangeModes",
    "IdentificationTypes",
    "IPAddressTypes",
    "TunnelMonitorActionChoices",
]

logger.info("✅ Nautobot Palo Alto VPN: Models & Constants Loaded Successfully")
