"""Forms for managing Tunnel Monitor Profiles in the Nautobot VPN app."""
# pylint: disable=too-many-ancestors, too-few-public-methods, too-many-locals, too-many-branches, too-many-statements

from django import forms
from nautobot.apps.forms import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotFilterForm,
    NautobotModelForm,
    TagFilterField,
)
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_app_vpn.models import TunnelMonitorActionChoices, TunnelMonitorProfile


class TunnelMonitorProfileForm(NautobotModelForm):
    """Form for creating and editing Tunnel Monitor Profiles."""

    tenant_group = DynamicModelChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        label="Tenant Group",
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label="Tenant",
        query_params={"tenant_group_id": "$tenant_group"},
    )
    action = forms.ChoiceField(
        choices=TunnelMonitorActionChoices.choices, widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = TunnelMonitorProfile
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "interval": forms.NumberInput(attrs={"class": "form-control"}),
            "threshold": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TunnelMonitorProfileFilterForm(NautobotFilterForm):
    """Form for importing Tunnel Monitor Profiles in bulk."""

    model = TunnelMonitorProfile
    tenant_group = DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        label="Tenant Group",
    )
    tenant = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label="Tenant",
        query_params={"tenant_group_id": "$tenant_group"},
    )
    tags = TagFilterField(model)
    action = forms.MultipleChoiceField(choices=TunnelMonitorActionChoices.choices, required=False)

    fieldsets = ((None, ("q", "tenant_group", "tenant", "tags", "action")),)
