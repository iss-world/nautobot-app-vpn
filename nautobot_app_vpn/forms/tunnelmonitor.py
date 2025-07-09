"""Forms for managing Tunnel Monitor Profiles in the Nautobot VPN app."""

from django import forms
from nautobot.apps.forms import NautobotFilterForm, NautobotModelForm  # Import necessary base forms

from nautobot_app_vpn.models import TunnelMonitorActionChoices, TunnelMonitorProfile


class TunnelMonitorProfileForm(NautobotModelForm):
    """Form for creating and editing Tunnel Monitor Profiles."""

    action = forms.ChoiceField(
        choices=TunnelMonitorActionChoices.choices, widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = TunnelMonitorProfile
        fields = [
            "name",
            "action",
            "interval",
            "threshold",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "interval": forms.NumberInput(attrs={"class": "form-control"}),
            "threshold": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TunnelMonitorProfileFilterForm(NautobotFilterForm):
    """Form for importing Tunnel Monitor Profiles in bulk."""

    model = TunnelMonitorProfile
    action = forms.MultipleChoiceField(choices=TunnelMonitorActionChoices.choices, required=False)
    # Add other fields for filtering if needed (q, interval, threshold range?)
    fieldsets = (
        (None, ("q", "action")),
        # ("Parameters", ("interval", "threshold")), # Example if range filters added
    )
