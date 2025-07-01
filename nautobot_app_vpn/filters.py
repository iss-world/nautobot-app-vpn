# nautobot_app_vpn/filters.py
import django_filters
from django.db.models import Q
from nautobot.apps.filters import (
    NautobotFilterSet,
    SearchFilter,
    StatusModelFilterSetMixin,
    TagFilter,
    MultiValueUUIDFilter,
)
from django_filters import ModelMultipleChoiceFilter, BooleanFilter, CharFilter

from nautobot.dcim.models import Device, Location, Interface, Platform
from nautobot.extras.filters import StatusFilter
from nautobot.extras.models import Status
from nautobot_app_vpn.models import (
    IKECrypto,
    IPSecCrypto,
    IKEGateway,
    IPSECTunnel,
    IPSecProxyID,
    TunnelMonitorProfile,
    TunnelMonitorActionChoices,
    TunnelRoleChoices,  # Import RoleChoices
)
from nautobot_app_vpn.models.constants import (  # Shortened for brevity
    EncryptionAlgorithms,
    AuthenticationAlgorithms,
    DiffieHellmanGroups,
    IPSECProtocols,
    IKEAuthenticationTypes,
    LifetimeUnits,
    IKEVersions,
    IKEExchangeModes,
    IdentificationTypes,
    IPAddressTypes,
)


class BaseFilterSet(StatusModelFilterSetMixin, NautobotFilterSet):
    # UPDATED: Removed "description": "icontains" from filter_predicates
    q = SearchFilter(
        filter_predicates={
            "name": "icontains",
        },
        label="Search",
    )


class IKECryptoFilterSet(BaseFilterSet):
    dh_group = django_filters.MultipleChoiceFilter(choices=DiffieHellmanGroups.choices)
    encryption = django_filters.MultipleChoiceFilter(choices=EncryptionAlgorithms.choices)
    authentication = django_filters.MultipleChoiceFilter(choices=AuthenticationAlgorithms.choices)
    lifetime = django_filters.RangeFilter()
    lifetime_unit = django_filters.ChoiceFilter(choices=LifetimeUnits.choices)

    class Meta:
        model = IKECrypto
        fields = [
            "id",
            "q",
            "name",
            "description",
            "dh_group",
            "encryption",
            "authentication",
            "lifetime",
            "lifetime_unit",
            "status",
        ]


class IPSecCryptoFilterSet(BaseFilterSet):
    encryption = django_filters.MultipleChoiceFilter(choices=EncryptionAlgorithms.choices)
    authentication = django_filters.MultipleChoiceFilter(choices=AuthenticationAlgorithms.choices)
    dh_group = django_filters.MultipleChoiceFilter(choices=DiffieHellmanGroups.choices)
    protocol = django_filters.MultipleChoiceFilter(choices=IPSECProtocols.choices)
    lifetime = django_filters.RangeFilter()
    lifetime_unit = django_filters.ChoiceFilter(choices=LifetimeUnits.choices)

    class Meta:
        model = IPSecCrypto
        fields = [
            "id",
            "q",
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


class IKEGatewayFilterSet(BaseFilterSet):
    local_devices = ModelMultipleChoiceFilter(
        field_name="local_devices", queryset=Device.objects.all(), label="Local Devices"
    )
    peer_devices = ModelMultipleChoiceFilter(
        queryset=Device.objects.all(), label="Peer Devices", required=False
    )  # Allow filtering with no peer
    local_locations = ModelMultipleChoiceFilter(
        queryset=Location.objects.all(), label="Local Locations", required=False
    )
    peer_locations = ModelMultipleChoiceFilter(queryset=Location.objects.all(), label="Peer Locations", required=False)
    peer_location_manual = django_filters.CharFilter(lookup_expr="icontains", label="Manual Peer Location")
    local_ip = django_filters.CharFilter(lookup_expr="icontains", label="Local IP/FQDN")
    peer_ip = django_filters.CharFilter(lookup_expr="icontains", label="Peer IP/FQDN")
    authentication_type = django_filters.MultipleChoiceFilter(
        choices=IKEAuthenticationTypes.choices, label="Authentication Type"
    )
    ike_crypto_profile = ModelMultipleChoiceFilter(queryset=IKECrypto.objects.all(), label="IKE Crypto Profile")
    ike_version = django_filters.MultipleChoiceFilter(choices=IKEVersions.choices, label="IKE Version")
    exchange_mode = django_filters.MultipleChoiceFilter(choices=IKEExchangeModes.choices, label="Exchange Mode")
    local_ip_type = django_filters.MultipleChoiceFilter(choices=IPAddressTypes.choices, label="Local IP Type")
    peer_ip_type = django_filters.MultipleChoiceFilter(choices=IPAddressTypes.choices, label="Peer IP Type")
    local_id_type = django_filters.MultipleChoiceFilter(choices=IdentificationTypes.choices, label="Local ID Type")
    peer_id_type = django_filters.MultipleChoiceFilter(choices=IdentificationTypes.choices, label="Peer ID Type")
    peer_device_manual = django_filters.CharFilter(lookup_expr="icontains", label="Manual Peer Name")
    bind_interface = ModelMultipleChoiceFilter(queryset=Interface.objects.all(), label="Bind Interface")
    enable_passive_mode = django_filters.BooleanFilter(label="Passive Mode Enabled")
    enable_nat_traversal = django_filters.BooleanFilter(label="NAT Traversal Enabled")
    enable_dpd = django_filters.BooleanFilter(label="DPD Enabled")
    local_platform = ModelMultipleChoiceFilter(
        field_name="local_platform", queryset=Platform.objects.all(), label="Local Platform(s)"
    )
    peer_platform = ModelMultipleChoiceFilter(
        field_name="peer_platform", queryset=Platform.objects.all(), label="Peer Platform(s)"
    )

    # Corrected Dummy filters with a method to prevent attempts to filter on model fields
    limit = CharFilter(method="do_nothing_filter", required=False, label="Limit")
    offset = CharFilter(method="do_nothing_filter", required=False, label="Offset")
    depth = CharFilter(method="do_nothing_filter", required=False, label="Depth")
    exclude_m2m = BooleanFilter(method="do_nothing_filter", required=False, label="Exclude M2M")

    class Meta:
        model = IKEGateway
        fields = [
            "id",
            "q",
            "name",
            "description",
            "local_devices",
            "peer_devices",
            "local_locations",
            "peer_locations",
            "peer_location_manual",
            "bind_interface",
            "local_ip",
            "peer_ip",
            "authentication_type",
            "ike_crypto_profile",
            "status",
            "ike_version",
            "exchange_mode",
            "local_ip_type",
            "peer_ip_type",
            "local_id_type",
            "peer_id_type",
            "peer_device_manual",
            "enable_passive_mode",
            "enable_nat_traversal",
            "enable_dpd",
            "local_platform",
            "peer_platform",
            "limit",
            "offset",
            "depth",
            "exclude_m2m",
        ]

    def do_nothing_filter(self, queryset, name, value):
        # This method is called for 'limit', 'offset', 'depth', and 'exclude_m2m'
        # because of the 'method' argument in their definitions.
        # It simply returns the queryset unchanged, preventing errors.
        return queryset


class TunnelMonitorProfileFilterSet(NautobotFilterSet):
    # Explicitly define q filter here
    q = SearchFilter(filter_predicates={"name": "icontains"}, label="Search")
    action = django_filters.MultipleChoiceFilter(choices=TunnelMonitorActionChoices.choices, label="Action")
    interval = django_filters.RangeFilter(label="Interval (seconds)")
    threshold = django_filters.RangeFilter(label="Threshold")

    class Meta:
        model = TunnelMonitorProfile
        # 'q' is defined above, 'status' not applicable
        fields = ["id", "name", "action", "interval", "threshold"]


class IPSECTunnelFilterSet(BaseFilterSet):  # Keep BaseFilterSet for Status
    # Add role filter
    role = django_filters.MultipleChoiceFilter(choices=TunnelRoleChoices.choices, label="Tunnel Role")
    # Keep existing filters
    devices = ModelMultipleChoiceFilter(queryset=Device.objects.all(), label="Devices")
    ike_gateway = ModelMultipleChoiceFilter(queryset=IKEGateway.objects.all(), label="IKE Gateway")
    ipsec_crypto_profile = ModelMultipleChoiceFilter(queryset=IPSecCrypto.objects.all(), label="IPSec Crypto Profile")
    tunnel_interface = ModelMultipleChoiceFilter(queryset=Interface.objects.all(), label="Tunnel Interface")
    # bind_interface = ModelMultipleChoiceFilter(queryset=Interface.objects.all(), label="Bind Interface")
    enable_tunnel_monitor = BooleanFilter(label="Monitor Enabled")
    monitor_destination_ip = django_filters.CharFilter(lookup_expr="icontains", label="Monitor Destination IP")
    monitor_profile = ModelMultipleChoiceFilter(queryset=TunnelMonitorProfile.objects.all(), label="Monitor Profile")

    class Meta:
        model = IPSECTunnel
        # Add 'role' to fields list
        fields = [
            "id",
            "q",
            "name",
            "description",
            "devices",
            "ike_gateway",
            "ipsec_crypto_profile",
            "tunnel_interface",
            "role",  # Added role
            "enable_tunnel_monitor",
            "monitor_destination_ip",
            "monitor_profile",
            "status",
        ]


class IPSecProxyIDFilterSet(NautobotFilterSet):
    tunnel = ModelMultipleChoiceFilter(queryset=IPSECTunnel.objects.all(), label="IPSec Tunnel")
    local_subnet = django_filters.CharFilter(lookup_expr="icontains")
    remote_subnet = django_filters.CharFilter(lookup_expr="icontains")
    protocol = django_filters.CharFilter(lookup_expr="icontains")
    local_port = django_filters.RangeFilter()
    remote_port = django_filters.RangeFilter()

    class Meta:
        model = IPSecProxyID
        fields = ["id", "tunnel", "local_subnet", "remote_subnet", "protocol", "local_port", "remote_port"]
