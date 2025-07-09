"""Forms for managing IKECrypto profiles in the Nautobot VPN app."""

from django import forms
from nautobot.apps.forms import NautobotFilterForm, NautobotModelForm

from nautobot_app_vpn.models import IKECrypto

# from nautobot.core.forms.widgets import APISelect


class IKECryptoForm(NautobotModelForm):
    """Form for creating and editing IKE Crypto profiles."""

    class Meta:
        model = IKECrypto
        fields = [
            "name",
            "description",
            "dh_group",
            "encryption",
            "authentication",
            "lifetime",
            "lifetime_unit",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Profile Name"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Optional description"}
            ),
            "dh_group": forms.Select(attrs={"class": "form-control"}),
            "encryption": forms.Select(attrs={"class": "form-control"}),
            "authentication": forms.Select(attrs={"class": "form-control"}),
            "lifetime": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Key lifetime in seconds"}),
            "lifetime_unit": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_name(self):
        """Prevent creating duplicates by name."""
        name = self.cleaned_data.get("name")
        if self.instance.pk is None and IKECrypto.objects.filter(name=name).exists():
            raise forms.ValidationError(f"A profile with the name '{name}' already exists.")
        return name


class IKECryptoFilterForm(NautobotFilterForm):
    """Import form for bulk uploading IKE Crypto profiles."""

    model = IKECrypto
    fieldsets = (
        (
            "IKE Crypto Filters",
            ("q", "encryption", "authentication", "dh_group", "lifetime", "lifetime_unit", "status"),
        ),
    )
