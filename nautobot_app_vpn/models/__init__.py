import logging

from .constants import (
    EncryptionAlgorithms,
    AuthenticationAlgorithms,
    DiffieHellmanGroups,
    IKEAuthenticationTypes,
    IPSECProtocols,
    LifetimeUnits,
    IKEVersions,
    IKEExchangeModes,
    IdentificationTypes,
    IPAddressTypes,
)
from .ikecrypto import IKECrypto
from .ikegateway import IKEGateway
from .ipseccrypto import IPSecCrypto
from .ipsectunnel import IPSECTunnel, IPSecProxyID,TunnelRoleChoices
from .vpn_dashboard import VPNDashboard
from .tunnelmonitor import TunnelMonitorProfile, TunnelMonitorActionChoices


# ✅ Logger for better debugging
logger = logging.getLogger(__name__)

__all__ = [
    # Models
    "IKECrypto",
    "IKEGateway",
    "IPSecCrypto",
    "IPSECTunnel",
    "IPSecProxyID",
    "TunnelRoleChoices",
    "VPNDashboard",
    "TunnelMonitorProfile",

    # Enum Constants
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
