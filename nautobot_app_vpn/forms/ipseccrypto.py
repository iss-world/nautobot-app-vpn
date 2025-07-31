"""Forms for managing IPSec Crypto profiles in the Nautobot VPN app."""
# pylint: disable=too-many-ancestors

from django import forms
from nautobot.apps.forms import (
    NautobotFilterForm,
    NautobotModelForm,
    DynamicModelMultipleChoiceField,
    APISelectMultiple,
)
from nautobot_app_vpn.models import IPSecCrypto
from nautobot_app_vpn.models.algorithms import (
    EncryptionAlgorithm,
    AuthenticationAlgorithm,
    DiffieHellmanGroup,
)


class IPSecCryptoForm(NautobotModelForm):
    """Form for adding and editing IPSec Crypto Profiles."""

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
        model = IPSecCrypto
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Profile Name"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Optional description"}
            ),
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
    """Import form for bulk uploading IPSec Crypto profiles."""

    model = IPSecCrypto

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
