# nautobot_app_vpn/tables.py
import django_tables2 as tables
from nautobot.apps.tables import (
    BaseTable,
    ToggleColumn,
    ButtonsColumn,
    StatusTableMixin,
    BooleanColumn,
    LinkedCountColumn,  # Ensure LinkedCountColumn is imported
)

# Import Location model for linking if desired
from nautobot.dcim.models import Location, Device, Interface  # Added Interface

# Import ALL necessary models
from nautobot_app_vpn.models import (
    IKECrypto,
    IPSecCrypto,
    IKEGateway,
    IPSECTunnel,
    IPSecProxyID,
    TunnelMonitorProfile,
    VPNDashboard,
)


class IKECryptoProfileTable(StatusTableMixin, BaseTable):
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(model=IKECrypto)

    class Meta(BaseTable.Meta):
        model = IKECrypto
        fields = (
            "pk",
            "name",
            "encryption",
            "authentication",
            "dh_group",
            "lifetime",
            "lifetime_unit",
            "status",
            "description",
            "actions",
        )
        default_columns = ("pk", "name", "encryption", "authentication", "dh_group", "status", "actions")


class IPSecCryptoProfileTable(StatusTableMixin, BaseTable):
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(model=IPSecCrypto)

    class Meta(BaseTable.Meta):
        model = IPSecCrypto
        fields = (
            "pk",
            "name",
            "encryption",
            "authentication",
            "dh_group",
            "protocol",
            "lifetime",
            "lifetime_unit",
            "status",
            "description",
            "actions",
        )
        default_columns = ("pk", "name", "encryption", "authentication", "dh_group", "protocol", "status", "actions")


class IKEGatewayTable(StatusTableMixin, BaseTable):
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    local_devices_display = tables.Column(accessor="local_device_names", verbose_name="Local Devices")
    local_locations_display = tables.Column(accessor="local_location_names", verbose_name="Local Locations")
    peer_identifier = tables.Column(accessor="peer_device_display", verbose_name="Peer Identifier(s)")
    peer_location_display = tables.Column(accessor="peer_location_display", verbose_name="Peer Location(s)")
    local_ip_type = tables.Column(verbose_name="Local IP Type")
    local_ip = tables.Column(verbose_name="Local IP/FQDN")
    peer_ip_type = tables.Column(verbose_name="Peer IP Type")
    peer_ip = tables.Column(verbose_name="Peer IP/FQDN")
    ike_version = tables.Column(verbose_name="IKE Ver.")
    authentication_type = tables.Column(verbose_name="Authentication")
    ike_crypto_profile = tables.Column(linkify=True)
    enable_nat_traversal = BooleanColumn(verbose_name="NAT-T")
    enable_passive_mode = BooleanColumn(verbose_name="Passive Mode")
    bind_interface = tables.Column(linkify=True, verbose_name="Bind If.")
    enable_dpd = BooleanColumn(verbose_name="DPD")
    local_platform = tables.Column(linkify=True, verbose_name="Local Platform")
    peer_platform = tables.Column(linkify=True, verbose_name="Peer Platform")
    actions = ButtonsColumn(model=IKEGateway, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = IKEGateway
        fields = (
            "pk",
            "name",
            "local_devices_display",
            "local_locations_display",
            "bind_interface",
            "local_ip_type",
            "local_ip",
            "peer_identifier",
            "peer_location_display",
            "peer_ip_type",
            "peer_ip",
            "ike_version",
            "authentication_type",
            "ike_crypto_profile",
            "enable_nat_traversal",
            "enable_dpd",
            "status",
            "description",
            "actions",
            "local_devices",
            "peer_devices",
            "local_locations",
            "peer_locations",
            "peer_device_manual",
            "peer_location_manual",
            "local_id_type",
            "local_id_value",
            "peer_id_type",
            "peer_id_value",
            "exchange_mode",
            "enable_passive_mode",
            "local_platform",
            "peer_platform",
            "dpd_interval",
            "dpd_retry",
            "liveness_check_interval",
        )
        default_columns = (
            "pk",
            "name",
            "local_devices_display",
            "local_platform",
            "local_ip",
            "peer_identifier",
            "peer_platform",
            "peer_ip",
            "ike_version",
            "authentication_type",
            "ike_crypto_profile",
            "status",
            "actions",
        )
        order_by = ("name",)


class TunnelMonitorProfileTable(BaseTable):  # No StatusMixin unless model has status
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    action = tables.Column(accessor="get_action_display")  # Use get_FIELD_display for choices
    interval = tables.Column(verbose_name="Interval (s)")
    threshold = tables.Column(verbose_name="Threshold")
    ipsectunnel_count = LinkedCountColumn(
        viewname="plugins:nautobot_app_vpn:ipsectunnel_list",
        url_params={"monitor_profile": "pk"},
        verbose_name="IPSec Tunnels",
    )
    actions = ButtonsColumn(model=TunnelMonitorProfile)

    class Meta(BaseTable.Meta):
        model = TunnelMonitorProfile
        fields = ("pk", "name", "action", "interval", "threshold", "ipsectunnel_count", "actions")
        default_columns = ("pk", "name", "action", "interval", "threshold", "ipsectunnel_count", "actions")


class IPSECTunnelTable(StatusTableMixin, BaseTable):
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    devices_display = tables.Column(accessor="device_names", verbose_name="Devices")
    role = tables.Column(order_by=("role"))  # Use get_FIELD_display for choices
    ike_gateway = tables.Column(linkify=True)
    ipsec_crypto_profile = tables.Column(linkify=True)
    tunnel_interface = tables.Column(linkify=True)
    enable_tunnel_monitor = BooleanColumn(verbose_name="Monitor")
    monitor_profile = tables.Column(linkify=True)
    proxy_id_count = tables.Column(accessor=tables.A("proxy_ids.count"), verbose_name="Proxy IDs")
    actions = ButtonsColumn(model=IPSECTunnel)

    class Meta(BaseTable.Meta):
        model = IPSECTunnel
        # Added 'role' to fields
        fields = (
            "pk",
            "name",
            "role",
            "devices_display",
            "ike_gateway",  # Added role
            "ipsec_crypto_profile",
            "tunnel_interface",
            "enable_tunnel_monitor",
            "monitor_destination_ip",  # Keep in available fields
            "monitor_profile",
            "proxy_id_count",
            "status",
            "description",
            "actions",
            "devices",  # devices M2M field itself if needed
        )
        # Added 'role' to default columns
        default_columns = (
            "pk",
            "name",
            "role",
            "devices_display",
            "ike_gateway",
            "ipsec_crypto_profile",  # Added role
            "tunnel_interface",
            "enable_tunnel_monitor",
            "status",
            "actions",
        )
        # Updated default ordering
        order_by = ("name", "role")


class IPSecProxyIDTable(BaseTable):  # No StatusMixin needed
    pk = ToggleColumn()
    tunnel = tables.Column(linkify=True)
    actions = ButtonsColumn(model=IPSecProxyID, pk_field="id")  # Changed pk_field to 'id'

    class Meta(BaseTable.Meta):
        model = IPSecProxyID
        fields = (
            "pk",
            "tunnel",
            "local_subnet",
            "remote_subnet",
            "protocol",
            "local_port",
            "remote_port",
            "actions",
        )
        default_columns = (
            "pk",
            "tunnel",
            "local_subnet",
            "remote_subnet",
            "protocol",
            "actions",
        )


class VPNDashboardTable(BaseTable):  # No StatusMixin needed
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(model=VPNDashboard)

    class Meta(BaseTable.Meta):
        model = VPNDashboard
        fields = (
            "pk",
            "name",
            "total_tunnels",
            "active_tunnels",
            "inactive_tunnels",
            "last_sync_status",
            "last_push_status",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "total_tunnels",
            "active_tunnels",
            "inactive_tunnels",
            "last_sync_status",
            "last_push_status",
            "actions",
        )
