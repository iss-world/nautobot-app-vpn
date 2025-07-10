"""Model definition for IKE Gateway configuration."""
# pylint: disable=too-many-ancestors

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from nautobot.core.models.generics import PrimaryModel

# Import Location model
from nautobot.dcim.models import Device, Location, Platform
from nautobot.extras.models import ChangeLoggedModel, StatusField
from nautobot.extras.utils import extras_features

from nautobot_app_vpn.models.constants import (
    IdentificationTypes,
    IKEAuthenticationTypes,
    IKEExchangeModes,
    IKEVersions,
    IPAddressTypes,
)
from nautobot_app_vpn.models.ikecrypto import IKECrypto
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
class IKEGateway(PrimaryModel, ChangeLoggedModel):
    """Model definition for IKE Gateway configuration."""

    name = models.CharField(
        max_length=100,
        # Consider if unique=True is still appropriate or needs adjustment
        help_text="Unique name for the IKE Gateway profile.",
    )
    description = models.TextField(blank=True, help_text="Optional description or purpose for this IKE Gateway.")

    # General Settings (No changes needed here)
    ike_version = models.CharField(
        max_length=20,
        choices=IKEVersions.choices,
        default=IKEVersions.IKEV2_PREFERRED,
        help_text="IKE protocol version.",
    )
    exchange_mode = models.CharField(
        max_length=15,
        choices=IKEExchangeModes.choices,
        default=IKEExchangeModes.AUTO,
        help_text="IKE exchange mode (primarily for IKEv1).",
    )

    # 🔹 Local Side Modifications
    local_ip_type = models.CharField(
        max_length=255,
        choices=IPAddressTypes.choices,
        default=IPAddressTypes.IP,
        help_text="Type of Local IP Address identification.",
    )
    local_ip = models.CharField(
        max_length=255, blank=True, help_text="Local IP address or FQDN (leave blank if type is Dynamic)."
    )
    # --- MODIFIED: ForeignKey to ManyToManyField ---
    local_devices = models.ManyToManyField(
        Device,
        related_name="local_ike_gateways",
        help_text="Associated local firewall devices (can select multiple for HA).",
        blank=False,  # Typically require at least one local device
    )
    # --- REMOVED: local_location CharField ---
    # --- ADDED: ManyToManyField for local locations ---
    local_locations = models.ManyToManyField(
        Location,
        related_name="local_ike_gateway_locations",
        help_text="Select the physical or logical locations of the local devices.",
        blank=True,  # Making locations optional
    )
    local_id_type = models.CharField(
        max_length=20,
        choices=IdentificationTypes.choices,
        blank=True,
        help_text="Type of local identifier (optional).",
    )
    local_id_value = models.CharField(
        max_length=255, blank=True, help_text="Value of the local identifier (IP, FQDN, etc.)."
    )

    # 🔹 Peer Side Modifications
    peer_ip_type = models.CharField(
        max_length=20,
        choices=IPAddressTypes.choices,
        default=IPAddressTypes.IP,
        help_text="Type of Peer IP Address identification.",
    )
    peer_ip = models.CharField(
        max_length=255, blank=True, help_text="Peer IP address or FQDN (leave blank if type is Dynamic)."
    )
    # --- MODIFIED: ForeignKey to ManyToManyField ---
    peer_devices = models.ManyToManyField(
        Device,
        related_name="peer_ike_gateways",
        help_text="Associated remote devices (optional, if known in Nautobot). Select multiple for HA.",
        blank=True,  # Peers might be external
    )
    peer_device_manual = models.CharField(
        max_length=255,
        blank=True,
        help_text="Specify Peer Name manually if Peer Devices are not selected or are external.",
    )

    peer_locations = models.ManyToManyField(
        Location,
        related_name="peer_ike_gateway_locations",
        help_text="Select the physical or logical locations of the peer devices (if known).",
        blank=True,
    )

    peer_location_manual = models.CharField(
        max_length=255,
        blank=True,
        help_text="Specify Peer Location manually if not selecting from existing Locations in the dropdown.",
    )
    peer_id_type = models.CharField(
        max_length=20,
        choices=IdentificationTypes.choices,
        blank=True,
        help_text="Type of peer identifier (optional).",
    )
    peer_id_value = models.CharField(
        max_length=255, blank=True, help_text="Value of the peer identifier (IP, FQDN, etc.)."
    )

    # Authentication (No changes needed here)
    authentication_type = models.CharField(
        max_length=20, choices=IKEAuthenticationTypes.choices, help_text="Authentication method for the IKE Gateway."
    )
    pre_shared_key = models.TextField(
        blank=True, help_text="Pre-Shared Key (⚠️ Store securely; consider Nautobot secrets integration)."
    )
    ike_crypto_profile = models.ForeignKey(
        IKECrypto,
        on_delete=models.PROTECT,
        related_name="ike_gateways",
        help_text="IKE Crypto Profile used for Phase 1.",
    )

    # Inside class IKEGateway(PrimaryModel, ChangeLoggedModel):
    bind_interface = models.ForeignKey(
        "dcim.Interface",
        on_delete=models.SET_NULL,
        null=True,
        related_name="ikegateway_binds",  # Use a distinct related_name
        help_text="Optional binding to a specific source interface (must exist on local devices).",
    )

    local_platform = models.ForeignKey(
        to=Platform,
        on_delete=models.SET_NULL,
        related_name="local_ike_gateways",  # Helps in querying from Platform back to IKEGateway
        null=True,
        verbose_name="Local Device Platform",
    )
    peer_platform = models.ForeignKey(
        to=Platform,
        on_delete=models.SET_NULL,
        related_name="peer_ike_gateways",  # Helps in querying from Platform back to IKEGateway
        null=True,
        verbose_name="Peer Device Platform",
    )

    natural_key_field_names = ["name"]

    # Advanced Options (No changes needed here)
    enable_passive_mode = models.BooleanField(default=False, help_text="Enable passive mode (responder only).")
    enable_nat_traversal = models.BooleanField(default=True, help_text="Enable NAT Traversal.")
    enable_dpd = models.BooleanField(default=True, help_text="Enable Dead Peer Detection (DPD).")
    dpd_interval = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text="DPD probe interval in seconds (if DPD enabled).",
    )
    dpd_retry = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="DPD retry count (if DPD enabled).",
    )
    liveness_check_interval = models.PositiveIntegerField(
        blank=True,
        default=5,
        validators=[MinValueValidator(1)],
        help_text="IKEv2 Liveness Check interval in seconds (optional, overrides DPD if set).",
    )

    # Nautobot Metadata (No changes needed here)
    status = StatusField(
        on_delete=models.PROTECT, related_name="%(app_label)s_%(class)s_related", default=get_default_status
    )
    last_sync = models.DateTimeField(blank=True, help_text="Last synchronization timestamp from the firewall.")

    class Meta:
        verbose_name = "IKE Gateway"
        verbose_name_plural = "IKE Gateways"
        ordering = ["name"]

        # Remove or update constraints if name uniqueness changes
        # constraints = [
        #     models.UniqueConstraint(fields=['local_device', 'name'], name='unique_ike_gateway_name_per_device')
        # ]

    def __str__(self):
        return self.name

    # --- Optional Helper Properties ---
    @property
    def local_device_names(self):
        """Returns comma-separated names of local devices."""
        return ", ".join([dev.name for dev in self.local_devices.all()])

    @property
    def peer_device_names(self):
        """Returns comma-separated names of peer devices."""
        return ", ".join([dev.name for dev in self.peer_devices.all()])

    @property
    def local_location_names(self):
        """Returns comma-separated names of local locations."""
        return ", ".join([loc.name for loc in self.local_locations.all()])

    @property
    def peer_location_display(self):
        """Returns combined peer location information."""
        selected_locs = ", ".join([loc.name for loc in self.peer_locations.all()])
        manual_loc = self.peer_location_manual

        if selected_locs and manual_loc:
            return f"Selected: {selected_locs} / Manual: {manual_loc}"
        if selected_locs:
            return selected_locs
        if manual_loc:
            return f"{manual_loc} (Manual)"
        return "—"

    @property
    def peer_device_display(self):
        """Returns combined peer device information with manual fallback."""
        devices = list(self.peer_devices.all())
        if devices:
            return ", ".join(str(dev) for dev in devices)
        if self.peer_device_manual:
            return f"{self.peer_device_manual} (Manual)"
        return "—"
