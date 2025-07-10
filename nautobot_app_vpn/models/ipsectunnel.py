"""Models for IPSec Tunnel objects and associated attributes."""
# pylint: disable=too-many-ancestors

from django.core.exceptions import ValidationError  # Import ValidationError
from django.db import models
from nautobot.core.models.generics import PrimaryModel
from nautobot.dcim.models import Device
from nautobot.extras.models import StatusField  # Assuming Status model is used
from nautobot.extras.utils import extras_features

from nautobot_app_vpn.utils import get_default_status  # Assuming you have this util

from .ikegateway import IKEGateway
from .ipseccrypto import IPSecCrypto
from .tunnelmonitor import TunnelMonitorProfile


class TunnelRoleChoices(models.TextChoices):
    """Choices for the role of an IPSec Tunnel in a redundant setup."""

    PRIMARY = "primary", "Primary"
    SECONDARY = "secondary", "Secondary"
    TERTIARY = "tertiary", "Tertiary"


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
class IPSECTunnel(PrimaryModel):
    """Model representing an IPSec Tunnel configuration."""

    name = models.CharField(max_length=100, help_text="Unique name for the IPSec Tunnel.")
    description = models.TextField(blank=True, help_text="Optional description.")

    devices = models.ManyToManyField(
        Device, related_name="ipsec_tunnels", help_text="Firewall device(s) associated with this IPSec Tunnel (for HA)."
    )

    ike_gateway = models.ForeignKey(
        IKEGateway,
        on_delete=models.PROTECT,
        related_name="ipsec_tunnels",
        help_text="IKE Gateway associated with this IPSec Tunnel.",
    )
    ipsec_crypto_profile = models.ForeignKey(
        IPSecCrypto,
        on_delete=models.PROTECT,
        related_name="ipsec_tunnels",
        help_text="IPSec Crypto Profile applied to this tunnel.",
    )
    tunnel_interface = models.ForeignKey(
        "dcim.Interface",
        on_delete=models.PROTECT,
        related_name="ipsec_tunnel_interfaces",
        help_text="Tunnel interface (e.g., tunnel.1) used. Should exist on *all* associated devices.",
    )

    enable_tunnel_monitor = models.BooleanField(default=False, help_text="Enable tunnel monitoring.")
    monitor_destination_ip = models.CharField(
        max_length=255,
        blank=True,
        help_text="Destination IP or FQDN to ping for monitoring.",
    )
    natural_key_field_names = ["name"]
    monitor_profile = models.ForeignKey(
        TunnelMonitorProfile,
        on_delete=models.SET_NULL,
        related_name="ipsec_tunnels",
        null=True,
        help_text="Tunnel Monitor Profile to use.",
    )

    role = models.CharField(
        max_length=50,
        choices=TunnelRoleChoices.choices,
        blank=True,  # Make it optional
        help_text="Role of this tunnel if part of a redundant setup (e.g., Primary, Backup).",
    )

    status = StatusField(
        on_delete=models.PROTECT, related_name="%(app_label)s_%(class)s_related", default=get_default_status
    )
    last_sync = models.DateTimeField(blank=True, help_text="Last synchronization timestamp.")

    class Meta:
        verbose_name = "IPSec Tunnel"
        verbose_name_plural = "IPSec Tunnels"
        ordering = ["name", "role"]

    def __str__(self):
        return self.name

    @property
    def device_names(self):
        """Return a comma-separated list of device names associated with this tunnel."""
        return ", ".join([dev.name for dev in self.devices.all()])

    def clean(self):
        super().clean()
        if self.enable_tunnel_monitor:
            if not self.monitor_destination_ip:
                raise ValidationError(
                    {"monitor_destination_ip": "Destination IP is required when tunnel monitoring is enabled."}
                )
            if not self.monitor_profile:
                raise ValidationError(
                    {"monitor_profile": "Monitor Profile is required when tunnel monitoring is enabled."}
                )


class IPSecProxyID(models.Model):
    """Model representing an IPSec Proxy ID configuration."""

    tunnel = models.ForeignKey(IPSECTunnel, on_delete=models.CASCADE, related_name="proxy_ids")
    local_subnet = models.CharField(max_length=50, blank=True)
    remote_subnet = models.CharField(max_length=50, blank=True)
    protocol = models.CharField(max_length=10, blank=True, default="any")
    local_port = models.PositiveIntegerField(blank=True, null=True)
    remote_port = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "IPSec Proxy ID"
        verbose_name_plural = "IPSec Proxy IDs"
        ordering = ["tunnel", "local_subnet", "remote_subnet"]

    def __str__(self):
        return f"{self.local_subnet or 'any'} <-> {self.remote_subnet or 'any'} ({self.protocol})"
