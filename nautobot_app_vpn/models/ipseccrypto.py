"""Models for IPsec Crypto profiles used in VPN configuration."""
# pylint: disable=too-many-ancestors

from django.db import models
from nautobot.core.models.generics import PrimaryModel
from nautobot.extras.models import ChangeLoggedModel, StatusField
from nautobot.extras.utils import extras_features

from nautobot_app_vpn.models.constants import (
    AuthenticationAlgorithms,
    DiffieHellmanGroups,
    EncryptionAlgorithms,
    IPSECProtocols,
    LifetimeUnits,
)
from nautobot_app_vpn.utils import get_default_status


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class IPSecCrypto(PrimaryModel, ChangeLoggedModel):
    """Global IPSec Crypto Profile shared across firewalls."""

    name = models.CharField(max_length=100, unique=True, help_text="Unique name for the IPSec Crypto Profile.")

    description = models.TextField(blank=True, help_text="Optional free-form description or usage notes.")

    encryption = models.CharField(
        max_length=50, choices=EncryptionAlgorithms.choices, help_text="Encryption algorithm used."
    )

    authentication = models.CharField(
        max_length=50, choices=AuthenticationAlgorithms.choices, help_text="Authentication algorithm used."
    )

    dh_group = models.CharField(
        max_length=50, choices=DiffieHellmanGroups.choices, help_text="Diffie-Hellman Group for key exchange."
    )

    protocol = models.CharField(
        max_length=5, choices=IPSECProtocols.choices, default=IPSECProtocols.ESP, help_text="IPSec protocol used."
    )

    lifetime = models.PositiveIntegerField(help_text="Lifetime duration (must be a positive number).")

    lifetime_unit = models.CharField(
        max_length=50,
        choices=LifetimeUnits.choices,
        default=LifetimeUnits.SECONDS,
        help_text="Unit of lifetime duration.",
    )

    status = StatusField(
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_related",
        default=get_default_status,
    )

    class Meta:
        verbose_name = "IPSec Crypto Profile"
        verbose_name_plural = "IPSec Crypto Profiles"
        ordering = ["name"]

    def __str__(self):
        return self.name
