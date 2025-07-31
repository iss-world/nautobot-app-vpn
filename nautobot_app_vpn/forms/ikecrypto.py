"""Forms for managing IKE Crypto profiles in the Nautobot VPN app."""
# pylint: disable=too-many-ancestors

from django import forms
from nautobot.apps.forms import (
    NautobotFilterForm,
    NautobotModelForm,
    DynamicModelMultipleChoiceField,
    APISelectMultiple,
)
from nautobot_app_vpn.models import IKECrypto
from nautobot_app_vpn.models.algorithms import (
    EncryptionAlgorithm,
    AuthenticationAlgorithm,
    DiffieHellmanGroup,
)


class IKECryptoForm(NautobotModelForm):
    """Form for creating and editing IKE Crypto profiles."""

    encryption = DynamicModelMultipleChoiceField(
        queryset=EncryptionAlgorithm.objects.all(),
        widget=APISelectMultiple(attrs={"class": "form-control"}),
        required=False,
        label="Encryption Algorithms",
    )
    authentication = DynamicModelMultipleChoiceField(
        queryset=AuthenticationAlgorithm.objects.all(),
        widget=APISelectMultiple(attrs={"class": "form-control"}),
        required=False,
        label="Authentication Algorithms",
    )
    dh_group = DynamicModelMultipleChoiceField(
        queryset=DiffieHellmanGroup.objects.all(),
        widget=APISelectMultiple(attrs={"class": "form-control"}),
        required=False,
        label="Diffie-Hellman Groups",
    )

    class Meta:
        model = IKECrypto
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Profile Name"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Optional description"}
            ),
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

    encryption = DynamicModelMultipleChoiceField(
        queryset=EncryptionAlgorithm.objects.all(),
        widget=APISelectMultiple,
        required=False,
        label="Encryption Algorithms",
    )
    authentication = DynamicModelMultipleChoiceField(
        queryset=AuthenticationAlgorithm.objects.all(),
        widget=APISelectMultiple,
        required=False,
        label="Authentication Algorithms",
    )
    dh_group = DynamicModelMultipleChoiceField(
        queryset=DiffieHellmanGroup.objects.all(),
        widget=APISelectMultiple,
        required=False,
        label="Diffie-Hellman Groups",
    )

    fieldsets = (
        (
            "IKE Crypto Filters",
            ("q", "encryption", "authentication", "dh_group", "lifetime", "lifetime_unit", "status"),
        ),
    )
