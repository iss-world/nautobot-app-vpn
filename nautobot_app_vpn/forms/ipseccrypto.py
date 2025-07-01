from django import forms
from nautobot.apps.forms import NautobotFilterForm, NautobotModelForm

from nautobot_app_vpn.models import IPSecCrypto

# from nautobot.core.forms.widgets import APISelect


class IPSecCryptoForm(NautobotModelForm):
    """Form for adding and editing IPSec Crypto Profiles."""

    # status = forms.ModelChoiceField(
    #     queryset=Status.objects.all(),
    #     required=False,
    #     help_text="Operational status of this IPSec Crypto Profile.",
    # )

    class Meta:
        model = IPSecCrypto
        fields = [
            "name",
            "description",
            "encryption",
            "authentication",
            "dh_group",
            "protocol",
            "lifetime",
            "lifetime_unit",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Profile Name"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Optional description"}
            ),
            "encryption": forms.Select(attrs={"class": "form-control"}),
            "authentication": forms.Select(attrs={"class": "form-control"}),
            "dh_group": forms.Select(attrs={"class": "form-control"}),
            "protocol": forms.Select(attrs={"class": "form-control"}),
            "lifetime": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Key lifetime in seconds"}),
            "lifetime_unit": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_name(self):
        """Prevent creating duplicates by name."""
        name = self.cleaned_data.get("name")
        if self.instance.pk is None and IPSecCrypto.objects.filter(name=name).exists():
            raise forms.ValidationError(f"A profile with the name '{name}' already exists.")
        return name


class IPSecCryptoFilterForm(NautobotFilterForm):
    """Filter form for IPSec Crypto Profiles."""

    model = IPSecCrypto
    fieldsets = (
        (
            "IPSec Crypto Profile Filters",
            (
                "q",
                "encryption",
                "authentication",
                "dh_group",
                "protocol",
                "lifetime",
                "lifetime_unit",
                "status",
            ),
        ),
    )
