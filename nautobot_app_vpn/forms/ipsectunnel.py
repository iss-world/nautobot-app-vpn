"""Forms for managing IPSec Tunnels in the Nautobot VPN app."""
# pylint: disable=too-many-ancestors, too-few-public-methods, too-many-locals, too-many-branches, too-many-statements

from django import forms
from django.forms.models import inlineformset_factory


from nautobot.apps.forms import (
    APISelectMultiple,  # Keep for 'devices' field
    BootstrapMixin,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotFilterForm,
    NautobotModelForm,
)
from nautobot.dcim.models import Device, Interface
from nautobot.extras.models import Status

# Import local models
from nautobot_app_vpn.models import (
    IKEGateway,
    IPSecCrypto,
    IPSecProxyID,
    IPSECTunnel,
    TunnelMonitorProfile,
    TunnelRoleChoices,
)


class IPSECTunnelForm(NautobotModelForm):
    """Form for creating and editing IPSec Tunnel configurations."""

    devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.filter(platform__name="PanOS"),  # Filter by platform name is safer
        label="Firewall Devices",
        required=True,
        widget=APISelectMultiple(attrs={"class": "form-control"}),  # Correct widget for M2M
    )
    ike_gateway = DynamicModelChoiceField(
        queryset=IKEGateway.objects.all(),
        label="IKE Gateway",
        query_params={"local_devices": "$devices"},
        help_text="Select an IKE Gateway. Filtered by selected devices.",
    )
    ipsec_crypto_profile = forms.ModelChoiceField(
        queryset=IPSecCrypto.objects.all().order_by("name"),  # Added ordering
        label="IPSec Crypto Profile",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    tunnel_interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),  # Broad base queryset
        label="Tunnel Interface (e.g., tunnel.1)",
        required=True,
        help_text="Select an existing tunnel interface. Filtered by selected devices.",
        query_params={"device_id": "$devices"},
    )
    status = forms.ModelChoiceField(  # <--- Explicitly defined
        queryset=Status.objects.all().order_by("name"),
        label="Status",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    role = forms.ChoiceField(
        choices=TunnelRoleChoices.choices,
        required=False,  # Make role optional
        label="Tunnel Role",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    enable_tunnel_monitor = forms.BooleanField(required=False, label="Enable Tunnel Monitor")
    monitor_destination_ip = forms.CharField(
        required=False,
        label="Monitor Destination IP / FQDN",
        widget=forms.TextInput(attrs={"placeholder": "e.g., 8.8.8.8"}),
    )
    monitor_profile = forms.ModelChoiceField(
        queryset=TunnelMonitorProfile.objects.all().order_by("name"),  # Added ordering
        label="Monitor Profile",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = IPSECTunnel
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            # No widget needed for bind_interface as it's removed
        }

    def clean(self):
        """Ensure selected interface exists and is valid."""

        super().clean()  # Call super().clean() first
        cleaned_data = getattr(self, "cleaned_data", None)
        if cleaned_data is None:
            return None

        monitor_enabled = cleaned_data.get("enable_tunnel_monitor")
        dest_ip = cleaned_data.get("monitor_destination_ip")
        profile = cleaned_data.get("monitor_profile")
        if monitor_enabled:
            if not dest_ip:
                self.add_error("monitor_destination_ip", "This field is required when tunnel monitoring is enabled.")
            if not profile:
                self.add_error("monitor_profile", "This field is required when tunnel monitoring is enabled.")

        tunnel_iface = cleaned_data.get("tunnel_interface")

        devices = cleaned_data.get("devices")
        if tunnel_iface and devices:
            if not hasattr(tunnel_iface, "device") or not tunnel_iface.device:
                pass
            elif tunnel_iface.device not in devices:
                self.add_error("tunnel_interface", "Selected Tunnel Interface does not belong to chosen device(s).")

        return cleaned_data


class IPSecProxyIDForm(BootstrapMixin, forms.ModelForm):
    """Form for creating and editing IPSec Proxy-ID entries."""

    class Meta:
        model = IPSecProxyID
        fields = [
            "local_subnet",
            "remote_subnet",
            "protocol",
            "local_port",
            "remote_port",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["local_subnet"].required = False
        self.fields["remote_subnet"].required = False
        self.fields["protocol"].required = False
        self.fields["protocol"].initial = "any"

    def clean(self):
        if not hasattr(self, "cleaned_data"):
            return None
        cleaned_data = self.cleaned_data
        local_subnet = cleaned_data.get("local_subnet")
        remote_subnet = cleaned_data.get("remote_subnet")
        if cleaned_data.get("DELETE", False):
            return cleaned_data
        field_values = [v for k, v in cleaned_data.items() if k not in ("DELETE", "id", "tunnel")]
        if not any(field_values):
            return cleaned_data
        has_other_details = any(
            v for k, v in cleaned_data.items() if k in ("protocol", "local_port", "remote_port") and v
        )
        if not local_subnet and not remote_subnet and has_other_details:
            raise forms.ValidationError(
                "At least one subnet (local or remote) must be provided if other Proxy ID details like protocol or ports are entered."
            )
        return cleaned_data


IPSecProxyIDFormSet = inlineformset_factory(
    parent_model=IPSECTunnel,
    model=IPSecProxyID,
    form=IPSecProxyIDForm,
    extra=1,
    can_delete=True,
)


class IPSECTunnelFilterForm(NautobotFilterForm):
    """Filter form for IPSECTunnel objects."""

    model = IPSECTunnel
    role = forms.MultipleChoiceField(choices=TunnelRoleChoices.choices, required=False)
    devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False, label="Devices")
    ike_gateway = DynamicModelChoiceField(queryset=IKEGateway.objects.all(), required=False, label="IKE Gateway")
    ipsec_crypto_profile = DynamicModelChoiceField(
        queryset=IPSecCrypto.objects.all(), required=False, label="IPSec Crypto Profile"
    )
    enable_tunnel_monitor = forms.NullBooleanField(
        required=False, widget=forms.Select(choices=[("", "---------"), ("true", "Yes"), ("false", "No")])
    )
    monitor_profile = DynamicModelChoiceField(
        queryset=TunnelMonitorProfile.objects.all(), required=False, label="Monitor Profile"
    )
    status = forms.ModelMultipleChoiceField(queryset=Status.objects.all(), required=False)
    # bind_interface field was not here, so no removal needed
    fieldsets = (
        ("Tunnel Filters", ("q", "devices", "ike_gateway", "role", "status")),
        ("Monitoring", ("enable_tunnel_monitor", "monitor_profile")),
    )
