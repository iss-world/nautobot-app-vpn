"""Serializers for Nautobot VPN Plugin."""
# pylint: disable=too-few-public-methods

from nautobot.apps.api import BaseModelSerializer, ChoiceField

# Import Location model
from nautobot.dcim.models import Device, Interface, Location, Platform
from nautobot.extras.models import Status
from rest_framework import serializers

from nautobot_app_vpn.models import (
    IKECrypto,
    IKEGateway,
    IPSecCrypto,
    IPSecProxyID,
    IPSECTunnel,
    TunnelMonitorActionChoices,
    TunnelMonitorProfile,
    TunnelRoleChoices,
    VPNDashboard,
)
from nautobot_app_vpn.models.constants import (
    IdentificationTypes,
    IKEAuthenticationTypes,
    IKEExchangeModes,
    IKEVersions,
    IPAddressTypes,
)


# --- Nested Serializers ---


class DummySerializer(serializers.Serializer):
    """Dummy serializer placeholder."""

    dummy = serializers.CharField()

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return validated_data


class VPNNestedDeviceSerializer(BaseModelSerializer):
    """Nested serializer for referencing a Device object."""

    url = serializers.HyperlinkedIdentityField(view_name="dcim-api:device-detail")

    class Meta:
        model = Device
        fields = ["id", "url", "display", "name"]


class VPNNestedLocationSerializer(BaseModelSerializer):
    """Nested serializer for referencing a Location object."""

    url = serializers.HyperlinkedIdentityField(view_name="dcim-api:location-detail")

    class Meta:
        model = Location
        fields = ["id", "url", "display", "name"]


class VPNNestedStatusSerializer(BaseModelSerializer):
    """Nested serializer for referencing a Status object."""

    url = serializers.HyperlinkedIdentityField(view_name="extras-api:status-detail")

    class Meta:
        model = Status
        fields = ["id", "url", "display", "name", "color"]


class VPNNestedIKECryptoSerializer(BaseModelSerializer):
    """Nested serializer for referencing an IKECrypto object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ikecrypto-detail")

    class Meta:
        model = IKECrypto
        fields = ["id", "url", "display", "name"]


class VPNNestedIPSecCryptoSerializer(BaseModelSerializer):
    """Nested serializer for referencing an IPSecCrypto object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ipseccrypto-detail")

    class Meta:
        model = IPSecCrypto
        fields = ["id", "url", "display", "name"]


class VPNNestedIKEGatewaySerializer(BaseModelSerializer):
    """Nested serializer for referencing an IKEGateway object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ikegateway-detail")

    class Meta:
        model = IKEGateway
        fields = ["id", "url", "display", "name"]


class VPNNestedInterfaceSerializer(BaseModelSerializer):
    """Nested serializer for referencing an Interface object."""

    url = serializers.HyperlinkedIdentityField(view_name="dcim-api:interface-detail")
    device = VPNNestedDeviceSerializer(read_only=True)  # Show device for context

    class Meta:
        model = Interface
        fields = ["id", "url", "display", "name", "device"]  # Added device


class VPNNestedIPSECTunnelSerializer(BaseModelSerializer):
    """Minimal serializer for related IPSECTunnel objects."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ipsectunnel-detail")

    class Meta:
        model = IPSECTunnel
        fields = ["id", "url", "display", "name"]


class VPNNestedTunnelMonitorProfileSerializer(BaseModelSerializer):
    """Minimal serializer for related TunnelMonitorProfile objects."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:tunnelmonitorprofile-detail")

    class Meta:
        model = TunnelMonitorProfile
        fields = ["id", "url", "display", "name"]


class VPNNestedPlatformSerializer(BaseModelSerializer):
    """Nested serializer for referencing a Platform object."""

    url = serializers.HyperlinkedIdentityField(view_name="dcim-api:platform-detail")

    class Meta:
        model = Platform
        fields = ["id", "url", "display", "name"]


class IKECryptoSerializer(BaseModelSerializer):
    """Serializer for IKECrypto objects."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ikecrypto-detail")
    status = VPNNestedStatusSerializer(required=False, allow_null=True, read_only=True)
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=Status.objects.all(), source="status", write_only=True, required=False, allow_null=True, label="Status"
    )

    class Meta:
        model = IKECrypto
        fields = [
            "id",
            "display",
            "url",
            "name",
            "dh_group",
            "encryption",
            "authentication",
            "lifetime",
            "lifetime_unit",
            "status",
            "status_id",
            "description",
            "created",
            "last_updated",
        ]
        read_only_fields = ["id", "display", "url", "status", "created", "last_updated"]


class IPSecCryptoSerializer(BaseModelSerializer):
    """Serializer for IPSecCrypto objects."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ipseccrypto-detail")
    status = VPNNestedStatusSerializer(required=False, allow_null=True, read_only=True)
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=Status.objects.all(), source="status", write_only=True, required=False, allow_null=True, label="Status"
    )

    class Meta:
        model = IPSecCrypto
        fields = [
            "id",
            "display",
            "url",
            "name",
            "encryption",
            "authentication",
            "dh_group",
            "protocol",
            "lifetime",
            "lifetime_unit",
            "status",
            "status_id",
            "description",
            "created",
            "last_updated",
        ]
        read_only_fields = ["id", "display", "url", "status", "created", "last_updated"]


class IKEGatewaySerializer(BaseModelSerializer):
    """Serializer for IKEGateway objects."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ikegateway-detail")

    # Read-only Nested Representations
    local_devices = VPNNestedDeviceSerializer(many=True, read_only=True)
    peer_devices = VPNNestedDeviceSerializer(many=True, read_only=True, required=False)
    local_locations = VPNNestedLocationSerializer(many=True, read_only=True, required=False)
    peer_locations = VPNNestedLocationSerializer(many=True, read_only=True, required=False)
    ike_crypto_profile = VPNNestedIKECryptoSerializer(read_only=True, required=False, allow_null=True)
    status = VPNNestedStatusSerializer(read_only=True, required=False, allow_null=True)
    # <<< ADDED: bind_interface read-only nested representation
    bind_interface = VPNNestedInterfaceSerializer(read_only=True, required=False, allow_null=True)
    local_platform = VPNNestedPlatformSerializer(read_only=True, required=False, allow_null=True)
    peer_platform = VPNNestedPlatformSerializer(read_only=True, required=False, allow_null=True)

    # Writeable Related Field Selectors
    local_device_ids = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source="local_devices",
        many=True,
        write_only=True,
        required=True,
        label="Local Devices (IDs)",
    )
    peer_device_ids = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source="peer_devices",
        many=True,
        write_only=True,
        required=False,
        label="Peer Devices (IDs)",
    )
    local_location_ids = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="local_locations",
        many=True,
        write_only=True,
        required=False,
        label="Local Locations (IDs)",
    )
    peer_location_ids = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="peer_locations",
        many=True,
        write_only=True,
        required=False,
        label="Peer Locations (IDs)",
    )
    ike_crypto_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=IKECrypto.objects.all(),
        source="ike_crypto_profile",
        write_only=True,
        required=True,
        allow_null=False,
        label="IKE Crypto Profile",
    )
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=Status.objects.all(), source="status", write_only=True, required=False, allow_null=True, label="Status"
    )

    bind_interface_id = serializers.PrimaryKeyRelatedField(
        queryset=Interface.objects.all(),
        source="bind_interface",
        write_only=True,
        required=False,
        allow_null=True,
        label="Bind Interface (ID)",
    )
    local_platform_id = serializers.PrimaryKeyRelatedField(
        queryset=Platform.objects.all(),
        source="local_platform",
        write_only=True,
        required=False,
        allow_null=True,
        label="Local Platform (ID)",
    )
    peer_platform_id = serializers.PrimaryKeyRelatedField(
        queryset=Platform.objects.all(),
        source="peer_platform",
        write_only=True,
        required=False,
        allow_null=True,
        label="Peer Platform (ID)",
    )

    # Choice Fields
    ike_version = ChoiceField(choices=IKEVersions.choices, required=False)
    exchange_mode = ChoiceField(choices=IKEExchangeModes.choices, required=False)
    local_ip_type = ChoiceField(choices=IPAddressTypes.choices, required=False)
    peer_ip_type = ChoiceField(choices=IPAddressTypes.choices, required=False)
    local_id_type = ChoiceField(choices=IdentificationTypes.choices, required=False, allow_null=True)
    peer_id_type = ChoiceField(choices=IdentificationTypes.choices, required=False, allow_null=True)
    authentication_type = ChoiceField(choices=IKEAuthenticationTypes.choices, required=False)

    # Other Fields
    pre_shared_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True, style={"input_type": "password"}
    )

    class Meta:
        model = IKEGateway
        fields = [
            "id",
            "display",
            "url",
            "name",
            "description",
            "ike_version",
            "exchange_mode",
            "local_ip_type",
            "local_ip",
            "local_devices",
            "local_device_ids",
            "local_locations",
            "local_location_ids",
            "local_platform",
            "local_platform_id",
            "local_id_type",
            "local_id_value",
            "peer_ip_type",
            "peer_ip",
            "peer_devices",
            "peer_device_ids",
            "peer_device_manual",
            "peer_locations",
            "peer_location_ids",
            "peer_location_manual",
            "peer_platform",
            "peer_platform_id",
            "peer_id_type",
            "peer_id_value",
            "authentication_type",
            "pre_shared_key",
            "ike_crypto_profile",
            "ike_crypto_profile_id",
            "bind_interface",
            "bind_interface_id",
            "enable_passive_mode",
            "enable_nat_traversal",
            "enable_dpd",
            "dpd_interval",
            "dpd_retry",
            "liveness_check_interval",
            "status",
            "status_id",
            "last_sync",
            "created",
            "last_updated",
        ]

        read_only_fields = [
            "id",
            "display",
            "url",
            "local_devices",
            "peer_devices",
            "local_locations",
            "peer_locations",
            "ike_crypto_profile",
            "status",
            "bind_interface",
            "local_platform",
            "peer_platform",
            "created",
            "last_updated",
            "last_sync",
        ]

    def validate(self, data):  # pylint: disable=arguments-renamed
        """Custom validation for IKEGateway serializer."""
        peer_locations = data.get("peer_locations")
        peer_location_manual = data.get("peer_location_manual")
        if peer_locations and peer_location_manual:
            raise serializers.ValidationError("Specify Peer Locations *or* Manual Peer Location, not both.")
        bind_iface_id = data.get("bind_interface")
        local_device_ids = data.get("local_devices")
        if bind_iface_id and local_device_ids:
            try:
                bind_iface_obj = Interface.objects.select_related("device").get(pk=bind_iface_id.pk)
                if bind_iface_obj.device.pk not in [dev.pk for dev in local_device_ids]:
                    raise serializers.ValidationError(
                        {
                            "bind_interface_id": "Selected Bind Interface must belong to one of the selected Local Devices."
                        }
                    )
            except Interface.DoesNotExist as exc:
                raise serializers.ValidationError({"bind_interface_id": "Invalid Bind Interface selected."}) from exc
        return data


class TunnelMonitorProfileSerializer(BaseModelSerializer):
    """Serializer for Tunnel Monitor Profiles."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:tunnelmonitorprofile-detail")
    action = ChoiceField(choices=TunnelMonitorActionChoices.choices, required=False)

    class Meta:
        model = TunnelMonitorProfile
        fields = ["id", "display", "url", "name", "action", "interval", "threshold", "created", "last_updated"]
        read_only_fields = ["id", "display", "url", "created", "last_updated"]


class IPSecProxyIDSerializer(BaseModelSerializer):
    """Serializer for IPSECTunnel model."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ipsecproxyid-detail")
    tunnel = VPNNestedIPSECTunnelSerializer(read_only=True)
    tunnel_id = serializers.PrimaryKeyRelatedField(
        queryset=IPSECTunnel.objects.all(),
        source="tunnel",
        write_only=True,
        required=True,
        allow_null=False,
        label="IPSec Tunnel",
    )

    class Meta:
        model = IPSecProxyID
        fields = [
            "id",
            "url",
            "display",
            "tunnel",
            "tunnel_id",
            "local_subnet",
            "remote_subnet",
            "protocol",
            "local_port",
            "remote_port",
        ]
        read_only_fields = ["id", "url", "display", "tunnel"]


class VPNDashboardSerializer(BaseModelSerializer):
    """Serializer for VPNDashboard objects."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:vpndashboard-detail")

    class Meta:
        model = VPNDashboard
        fields = [
            "id",
            "url",
            "display",
            "name",
            "last_updated",
            "total_tunnels",
            "active_tunnels",
            "inactive_tunnels",
            "last_sync_status",
            "last_sync_time",
            "last_push_status",
            "last_push_time",
            "created",
        ]
        read_only_fields = ["id", "url", "display", "created", "last_updated"]


class IPSECTunnelSerializer(BaseModelSerializer):
    """Serializer for IPSECTunnel objects."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_app_vpn-api:ipsectunnel-detail")

    devices = VPNNestedDeviceSerializer(many=True, read_only=True)
    ike_gateway = VPNNestedIKEGatewaySerializer(read_only=True, required=False, allow_null=True)
    ipsec_crypto_profile = VPNNestedIPSecCryptoSerializer(read_only=True, required=False, allow_null=True)
    status = VPNNestedStatusSerializer(read_only=True, required=False, allow_null=True)
    tunnel_interface = VPNNestedInterfaceSerializer(read_only=True, required=False, allow_null=True)
    monitor_profile = VPNNestedTunnelMonitorProfileSerializer(read_only=True, required=False, allow_null=True)
    proxy_ids = IPSecProxyIDSerializer(many=True, read_only=True)
    role = ChoiceField(choices=TunnelRoleChoices.choices, required=False, allow_null=True)

    device_ids = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source="devices",
        many=True,
        write_only=True,
        required=True,
        label="Devices (IDs)",
    )
    ike_gateway_id = serializers.PrimaryKeyRelatedField(
        queryset=IKEGateway.objects.all(),
        source="ike_gateway",
        write_only=True,
        required=True,
        allow_null=False,
        label="IKE Gateway",
    )
    ipsec_crypto_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=IPSecCrypto.objects.all(),
        source="ipsec_crypto_profile",
        write_only=True,
        required=True,
        allow_null=False,
        label="IPSec Crypto Profile",
    )
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=Status.objects.all(), source="status", write_only=True, required=False, allow_null=True, label="Status"
    )
    tunnel_interface_id = serializers.PrimaryKeyRelatedField(
        queryset=Interface.objects.all(),
        source="tunnel_interface",
        write_only=True,
        required=True,
        allow_null=False,
        label="Tunnel Interface",
    )

    monitor_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=TunnelMonitorProfile.objects.all(),
        source="monitor_profile",
        write_only=True,
        required=False,
        allow_null=True,
        label="Monitor Profile (ID)",
    )

    class Meta:
        model = IPSECTunnel
        fields = [
            "id",
            "display",
            "url",
            "name",
            "description",
            "devices",
            "device_ids",
            "ike_gateway",
            "ike_gateway_id",
            "ipsec_crypto_profile",
            "ipsec_crypto_profile_id",
            "tunnel_interface",
            "tunnel_interface_id",
            "role",
            "proxy_ids",
            "enable_tunnel_monitor",
            "monitor_destination_ip",
            "monitor_profile",
            "monitor_profile_id",
            "status",
            "status_id",
            "last_sync",
            "created",
            "last_updated",
        ]

        read_only_fields = [
            "id",
            "display",
            "url",
            "devices",
            "ike_gateway",
            "ipsec_crypto_profile",
            "status",
            "tunnel_interface",
            "monitor_profile",
            "proxy_ids",
            "created",
            "last_updated",
            "last_sync",
        ]

    def validate(self, data):  # pylint: disable=arguments-renamed
        """Custom validation for IPSECTunnel serializer."""
        monitor_enabled = data.get(
            "enable_tunnel_monitor", getattr(self.instance, "enable_tunnel_monitor", False) if self.instance else False
        )
        dest_ip = data.get(
            "monitor_destination_ip", getattr(self.instance, "monitor_destination_ip", None) if self.instance else None
        )
        profile_id_submitted = "monitor_profile_id" in data

        if monitor_enabled:
            if not dest_ip:
                raise serializers.ValidationError(
                    {"monitor_destination_ip": "Destination IP is required when tunnel monitoring is enabled."}
                )

            if profile_id_submitted and data.get("monitor_profile_id") is None:
                raise serializers.ValidationError(
                    {"monitor_profile_id": "Monitor Profile is required when tunnel monitoring is enabled."}
                )

            if not self.instance and "monitor_profile_id" not in data:
                raise serializers.ValidationError(
                    {"monitor_profile_id": "Monitor Profile is required when tunnel monitoring is enabled."}
                )

            if self.instance and profile_id_submitted and data.get("monitor_profile_id") is None and monitor_enabled:
                raise serializers.ValidationError(
                    {"monitor_profile_id": "Cannot remove Monitor Profile while tunnel monitoring is enabled."}
                )
        return data
