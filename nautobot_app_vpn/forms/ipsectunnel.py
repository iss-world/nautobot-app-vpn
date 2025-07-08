"""Module for defining IPsec Tunnel forms used in the VPN plugin."""

from django import forms
from django.forms.models import inlineformset_factory

# Import necessary Nautobot components
from nautobot.apps.forms import (
    APISelectMultiple,  # Keep for 'devices' field
    BootstrapMixin,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotFilterForm,
    NautobotModelForm,
)
from nautobot.dcim.models import Device, Interface

# Corrected Imports Below:
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


# 🔹 IPSec Tunnel Main Form (UPDATED - Removed bind_interface)
class IPSECTunnelForm(NautobotModelForm):
    """Form for configuring IPSec Tunnels."""

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
    # --- REMOVED bind_interface DynamicModelChoiceField ---
    # bind_interface = DynamicModelChoiceField(...) # This section is deleted

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
    # status = DynamicModelChoiceField(...) # Keep commented out or implement as needed

    class Meta:
        model = IPSECTunnel
        fields = [
            "name",
            "description",
            "devices",
            "ike_gateway",
            "ipsec_crypto_profile",
            "tunnel_interface",  # "bind_interface", removed from here
            "role",
            "enable_tunnel_monitor",
            "monitor_destination_ip",
            "monitor_profile",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            # No widget needed for bind_interface as it's removed
        }

    # --- Main clean method ---
    def clean(self):
        super().clean()  # Call super().clean() first
        cleaned_data = getattr(self, "cleaned_data", None)
        if cleaned_data is None:
            return None

        # Validation for tunnel monitoring fields (Keep this)
        monitor_enabled = cleaned_data.get("enable_tunnel_monitor")
        dest_ip = cleaned_data.get("monitor_destination_ip")
        profile = cleaned_data.get("monitor_profile")
        if monitor_enabled:
            if not dest_ip:
                self.add_error("monitor_destination_ip", "This field is required when tunnel monitoring is enabled.")
            if not profile:
                self.add_error("monitor_profile", "This field is required when tunnel monitoring is enabled.")

        # --- REMOVED bind_interface validation logic ---
        tunnel_iface = cleaned_data.get("tunnel_interface")
        # bind_iface = cleaned_data.get("bind_interface") # Removed
        # # Check comparing tunnel_iface and bind_iface is removed
        # if tunnel_iface and bind_iface and tunnel_iface == bind_iface:
        #     self.add_error(...) # Removed

        # Check for tunnel_interface device ownership (Keep this)
        devices = cleaned_data.get("devices")
        if tunnel_iface and devices:
            if not hasattr(tunnel_iface, "device") or not tunnel_iface.device:
                pass  # Interface might not have a device assigned (less common for tunnels)
            elif tunnel_iface.device not in devices:
                self.add_error("tunnel_interface", "Selected Tunnel Interface does not belong to chosen device(s).")

        # --- REMOVED bind_interface device ownership check ---
        # if bind_iface and devices:
        #    (...) self.add_error('bind_interface', ...) # Removed

        # Important: Return the cleaned_data dictionary
        return cleaned_data

    # --- END main clean method ---


# 🔹 Proxy ID Entry Form (Keep as is)
class IPSecProxyIDForm(BootstrapMixin, forms.ModelForm):
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


# 🔹 Inline formset for use in UI view (Keep as is)
IPSecProxyIDFormSet = inlineformset_factory(
    parent_model=IPSECTunnel,
    model=IPSecProxyID,
    form=IPSecProxyIDForm,
    extra=1,
    can_delete=True,
)


# 🔹 IPSec Tunnel Filter Form (Keep as is, no bind_interface was present)
class IPSECTunnelFilterForm(NautobotFilterForm):
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
