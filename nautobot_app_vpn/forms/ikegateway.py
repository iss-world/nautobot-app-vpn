"""Forms for managing IKE Gateway profiles in the Nautobot VPN app."""
# pylint: disable=too-many-ancestors, too-few-public-methods, too-many-locals, too-many-branches, too-many-statements

import re

from django import forms
from django.core.exceptions import ValidationError as CoreValidationError
from django.core.validators import MinLengthValidator
from django.db import models

# Import necessary Nautobot form components and models
from nautobot.apps.forms import (
    APISelectMultiple,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotFilterForm,
    NautobotModelForm,
    SmallTextarea,
)
from nautobot.dcim.models import Device, Interface, Location, Platform  # Need Location AND Interface
from nautobot.extras.models import Status

# Import local models and constants
from nautobot_app_vpn.models import IKECrypto, IKEGateway
from nautobot_app_vpn.models.constants import (
    IKEAuthenticationTypes,
    IKEVersions,
    IPAddressTypes,
)


class IKEGatewayForm(NautobotModelForm):
    """Form for creating and editing IKE Gateway profiles."""

    local_devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.filter(platform__name="PanOS"),  # Base queryset
        label="Local Devices",
        required=True,  # Restore requirement
        widget=APISelectMultiple(attrs={"class": "form-control"}),
    )
    peer_devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        label="Peer Devices",
        required=False,
        widget=APISelectMultiple(attrs={"class": "form-control"}),
    )
    local_locations = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        label="Local Locations",
        required=False,
        widget=APISelectMultiple(attrs={"class": "form-control"}),
    )
    peer_locations = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        label="Peer Locations",
        required=False,
        widget=APISelectMultiple(attrs={"class": "form-control"}),
    )

    local_ip_type = forms.ChoiceField(
        choices=[("", "---------")] + IPAddressTypes.choices,
        required=True,
        label="Local IP Type",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    peer_ip_type = forms.ChoiceField(
        choices=[("", "---------")] + IPAddressTypes.choices,
        required=True,
        label="Peer IP Type",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    pre_shared_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={"class": "form-control", "placeholder": "Enter pre-shared key (leave blank to keep unchanged)"},
        ),
        help_text="Required for PSK authentication when creating. Stored securely if secrets backend is configured.",
        validators=[MinLengthValidator(8)],
    )
    peer_location_manual = forms.CharField(
        required=False,
        label="Manual Peer Location",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter if Peer Location not in dropdown"}
        ),
        help_text="Use this if the peer's location isn't an existing Nautobot Location.",
    )
    peer_device_manual = forms.CharField(
        required=False,
        label="Manual Peer Device",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Specify if peer device(s) not selected"}
        ),
    )
    ike_crypto_profile = forms.ModelChoiceField(
        queryset=IKECrypto.objects.all(),
        label="IKE Crypto Profile",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    bind_interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),  # Base queryset
        label="Bind Interface (Optional)",
        required=False,
        help_text="Select source interface for IKE traffic. Filtered by selected local devices.",
        query_params={"device_id": "$local_devices"},
    )

    local_platform = DynamicModelChoiceField(
        queryset=Platform.objects.all(),
        label="Local Platform",
        required=False,
    )
    peer_platform = DynamicModelChoiceField(
        queryset=Platform.objects.all(),
        label="Peer Platform",
        required=False,
    )

    class Meta:
        model = IKEGateway
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": SmallTextarea(attrs={"rows": 3}),
            "ike_version": forms.Select(attrs={"class": "form-control"}),
            "exchange_mode": forms.Select(attrs={"class": "form-control"}),
            "local_ip": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Required if Type is IP or FQDN"}
            ),
            "local_id_type": forms.Select(attrs={"class": "form-control", "required": False}),
            "local_id_value": forms.TextInput(attrs={"class": "form-control"}),
            "peer_ip": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Required if Type is IP or FQDN"}
            ),
            "peer_device_manual": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Specify if peer device(s) not selected"}
            ),
            "peer_id_type": forms.Select(attrs={"class": "form-control", "required": False}),
            "peer_id_value": forms.TextInput(attrs={"class": "form-control"}),
            "authentication_type": forms.Select(attrs={"class": "form-control"}),
            "ike_crypto_profile": forms.Select(attrs={"class": "form-control"}),
            "enable_passive_mode": forms.CheckboxInput(),
            "enable_nat_traversal": forms.CheckboxInput(),
            "enable_dpd": forms.CheckboxInput(),
            "dpd_interval": forms.NumberInput(attrs={"class": "form-control"}),
            "dpd_retry": forms.NumberInput(attrs={"class": "form-control"}),
            "liveness_check_interval": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        """Customize initialization for dynamic field options."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if "pre_shared_key" in self.fields:
                self.fields["pre_shared_key"].required = False
                self.fields["pre_shared_key"].widget.attrs["placeholder"] = "Leave blank to keep unchanged"

    def clean(self):
        """Custom form validation. Bypasses super().clean() due to M2M field issues.
        Manually triggers model validation via instance.full_clean().
        """

        cleaned_data = self.cleaned_data

        if not cleaned_data:
            raise forms.ValidationError("Form data dictionary is unexpectedly empty.")

        # --- Existing Validation ---
        peer_locations = cleaned_data.get("peer_locations")
        peer_location_manual = cleaned_data.get("peer_location_manual")
        auth_type = cleaned_data.get("authentication_type")
        ps_key = cleaned_data.get("pre_shared_key")
        is_new = not (self.instance and self.instance.pk)
        local_ip_type = cleaned_data.get("local_ip_type")
        peer_ip_type = cleaned_data.get("peer_ip_type")

        local_ip_value = cleaned_data.get("local_ip")
        local_ip = local_ip_value.strip() if local_ip_value is not None else ""
        peer_ip_value = cleaned_data.get("peer_ip")
        peer_ip = peer_ip_value.strip() if peer_ip_value is not None else ""

        if peer_locations and peer_location_manual:
            self.add_error(None, "Please select Peer Locations *or* enter a Manual Peer Location, not both.")

        if auth_type == IKEAuthenticationTypes.PSK and is_new and not ps_key:
            self.add_error("pre_shared_key", "A Pre-Shared Key is required for PSK authentication when creating.")

        def is_valid_ip_or_subnet_or_fqdn(val):
            # Match IPv4, IPv4/CIDR, IPv6, IPv6/CIDR, or a basic FQDN
            ip_regex = r"^([0-9a-fA-F:.]+)(/\d{1,3})?$"
            fqdn_regex = r"^([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+$"
            return re.match(ip_regex, val) or re.match(fqdn_regex, val)

        if local_ip_type == IPAddressTypes.IP:
            if not local_ip:
                self.add_error("local_ip", "Local IP address value is required.")
            elif not is_valid_ip_or_subnet_or_fqdn(local_ip):
                self.add_error("local_ip", "Enter a valid IP address, subnet, or FQDN.")
        elif local_ip_type == IPAddressTypes.FQDN:
            if not local_ip:
                self.add_error("local_ip", "Local FQDN value is required.")
        elif local_ip_type == IPAddressTypes.DYNAMIC and local_ip:
            if not self.errors.get("local_ip"):
                cleaned_data["local_ip"] = ""

        if peer_ip_type == IPAddressTypes.IP:
            if not peer_ip:
                self.add_error("peer_ip", "Peer IP address value is required.")
            elif not is_valid_ip_or_subnet_or_fqdn(peer_ip):
                self.add_error("peer_ip", "Enter a valid IP address, subnet, or FQDN.")
        elif peer_ip_type == IPAddressTypes.FQDN:
            if not peer_ip:
                self.add_error("peer_ip", "Peer FQDN value is required.")
        elif peer_ip_type == IPAddressTypes.DYNAMIC and peer_ip:
            if not self.errors.get("peer_ip"):
                cleaned_data["peer_ip"] = ""

        bind_iface = cleaned_data.get("bind_interface")
        local_devs = cleaned_data.get("local_devices")
        if bind_iface and local_devs:
            if not hasattr(bind_iface, "device") or not bind_iface.device:
                pass
            elif bind_iface.device not in local_devs:
                self.add_error(
                    "bind_interface", "Selected Bind Interface must belong to one of the selected Local Devices."
                )

        if self._errors:
            return cleaned_data

        temp_instance = self.instance if self.instance.pk else self.Meta.model()
        m2m_fields = ["local_devices", "peer_devices", "local_locations", "peer_locations"]
        # Ensure 'bind_interface' is included in fields_to_set if it wasn't already
        fields_to_set = [f for f in self.Meta.fields if f not in m2m_fields]

        for field_name in fields_to_set:
            if field_name in cleaned_data:
                # Handle potential None for boolean fields if checkboxes aren't checked
                if isinstance(temp_instance._meta.get_field(field_name), forms.BooleanField):
                    setattr(temp_instance, field_name, cleaned_data.get(field_name, False))
                # Handle ForeignKey fields (like bind_interface)
                elif isinstance(temp_instance._meta.get_field(field_name), models.ForeignKey):
                    setattr(temp_instance, field_name, cleaned_data[field_name])
                else:
                    setattr(temp_instance, field_name, cleaned_data[field_name])

        try:
            # Exclude M2M fields and the new FK from model validation here
            # as FK relations are handled by the form field directly.
            temp_instance.full_clean(
                exclude=m2m_fields + ["bind_interface"]
            )  # Exclude bind_interface from full_clean check
        except CoreValidationError as e:
            self._update_errors(e)  # Add model validation errors to the form

        return cleaned_data


# Filter Form definition (No changes needed here unless you want to filter by bind_interface)
class IKEGatewayFilterForm(NautobotFilterForm):
    """Filter form for IKE Gateway profiles in the Nautobot VPN app."""

    model = IKEGateway
    q = forms.CharField(required=False, label="Search")
    local_devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.filter(platform__name="PanOS"), required=False, label="Local Devices"
    )
    peer_devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False, label="Peer Devices")
    local_locations = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(), required=False, label="Local Locations"
    )
    peer_locations = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(), required=False, label="Peer Locations"
    )
    peer_location_manual = forms.CharField(required=False, label="Manual Peer Location")
    ike_version = forms.ChoiceField(choices=[("", "---------")] + IKEVersions.choices, required=False)
    authentication_type = forms.ChoiceField(
        choices=[("", "---------")] + IKEAuthenticationTypes.choices, required=False
    )
    status = forms.ModelMultipleChoiceField(queryset=Status.objects.all(), required=False)
    # Optional: Add bind_interface filter
    # bind_interface = DynamicModelMultipleChoiceField(queryset=Interface.objects.all(), required=False, label="Bind Interface")

    fieldsets = (
        ("Search", ("q",)),
        (
            "Identification",
            ("local_devices", "peer_devices", "local_locations", "peer_locations", "peer_location_manual"),
        ),
        ("Parameters", ("ike_version", "authentication_type", "status", "local_platform", "peer_platform")),
    )
