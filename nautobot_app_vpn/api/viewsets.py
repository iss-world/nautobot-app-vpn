"""API viewsets for the Nautobot VPN plugin."""
# pylint: disable=too-many-ancestors, too-many-locals, too-many-branches, too-many-statements, too-many-nested-blocks

import logging
from django.apps import apps
from django.conf import settings
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from neo4j import GraphDatabase
from neo4j import exceptions as neo4j_exceptions

from nautobot.dcim.models import Platform
from nautobot_app_vpn.api.pagination import StandardResultsSetPagination
from nautobot_app_vpn.api.permissions import IsAdminOrReadOnly


from nautobot_app_vpn.api.serializers import (
    IKECryptoSerializer,
    IKEGatewaySerializer,
    IPSecCryptoSerializer,
    IPSecProxyIDSerializer,
    IPSECTunnelSerializer,
    TunnelMonitorProfileSerializer,
    DummySerializer,
)

from nautobot_app_vpn.filters import (
    IKECryptoFilterSet,
    IKEGatewayFilterSet,
    IPSecCryptoFilterSet,
    IPSecProxyIDFilterSet,
    IPSECTunnelFilterSet,
    TunnelMonitorProfileFilterSet,
)

from nautobot_app_vpn.models import (
    IKECrypto,
    IKEGateway,
    IPSecCrypto,
    IPSecProxyID,
    IPSECTunnel,
    TunnelMonitorProfile,
    VPNDashboard,
)

from nautobot_app_vpn.models.algorithms import (
    EncryptionAlgorithm,
    AuthenticationAlgorithm,
    DiffieHellmanGroup,
)
from nautobot_app_vpn.api.serializers import (
    EncryptionAlgorithmSerializer,
    AuthenticationAlgorithmSerializer,
    DiffieHellmanGroupSerializer,
)


logger = logging.getLogger(__name__)


class EncryptionAlgorithmViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for Encryption Algorithms."""

    queryset = EncryptionAlgorithm.objects.all()
    serializer_class = EncryptionAlgorithmSerializer


class AuthenticationAlgorithmViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for Authentication Algorithms."""

    queryset = AuthenticationAlgorithm.objects.all()
    serializer_class = AuthenticationAlgorithmSerializer


class DiffieHellmanGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for Diffie-Hellman Groups."""

    queryset = DiffieHellmanGroup.objects.all()
    serializer_class = DiffieHellmanGroupSerializer


class IKECryptoViewSet(viewsets.ModelViewSet):
    """API endpoint for managing IKE Crypto Profiles."""

    queryset = IKECrypto.objects.all().order_by("name")
    serializer_class = IKECryptoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = IKECryptoFilterSet
    ordering_fields = ["name", "dh_group", "encryption", "lifetime"]
    search_fields = ["name", "dh_group", "encryption"]
    pagination_class = StandardResultsSetPagination


class IPSecCryptoViewSet(viewsets.ModelViewSet):
    """API endpoint for managing IPSec Crypto Profiles."""

    queryset = IPSecCrypto.objects.all().order_by("name")
    serializer_class = IPSecCryptoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = IPSecCryptoFilterSet
    ordering_fields = ["name", "encryption", "authentication", "dh_group"]
    search_fields = ["name", "encryption", "authentication"]
    pagination_class = StandardResultsSetPagination


class IKEGatewayViewSet(viewsets.ModelViewSet):
    """API viewset for IKE Gateways."""

    queryset = (
        IKEGateway.objects.select_related(
            "ike_crypto_profile",
            "status",
            "bind_interface",
        )
        .prefetch_related("local_devices", "peer_devices", "local_locations", "peer_locations")
        .order_by("name")
    )

    serializer_class = IKEGatewaySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = IKEGatewayFilterSet
    ordering_fields = ["name", "local_ip", "peer_ip", "bind_interface__name"]

    search_fields = [
        "name",
        "description",
        "local_ip",
        "peer_ip",
        "peer_device_manual",
        "peer_location_manual",
        "bind_interface__name",
    ]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class TunnelMonitorProfileViewSet(viewsets.ModelViewSet):
    """API viewset for Tunnel Monitor Profiles."""

    queryset = TunnelMonitorProfile.objects.all().order_by("name")
    serializer_class = TunnelMonitorProfileSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = TunnelMonitorProfileFilterSet
    ordering_fields = ["name", "action", "interval", "threshold"]
    search_fields = ["name"]
    pagination_class = StandardResultsSetPagination


class IPSECTunnelViewSet(viewsets.ModelViewSet):
    """API viewset for IPSec Tunnels."""

    queryset = (
        IPSECTunnel.objects.select_related(
            "ike_gateway",
            "ipsec_crypto_profile",
            "status",
            "tunnel_interface",
            "monitor_profile",
        )
        .prefetch_related(
            "devices",
            "proxy_ids",
        )
        .order_by("name")
        .distinct()
    )

    serializer_class = IPSECTunnelSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = IPSECTunnelFilterSet

    ordering_fields = [
        "name",
        "ike_gateway__name",
        "ipsec_crypto_profile__name",
        "tunnel_interface__name",
        "status__name",
        "enable_tunnel_monitor",
        "monitor_destination_ip",
    ]
    search_fields = [
        "name",
        "description",
        "ike_gateway__name",
        "ipsec_crypto_profile__name",
        "tunnel_interface__name",
        "monitor_destination_ip",
    ]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class IPSecProxyIDViewSet(viewsets.ModelViewSet):
    """API viewset for IPSec Proxy IDs."""

    queryset = IPSecProxyID.objects.select_related("tunnel").order_by("tunnel__name")
    serializer_class = IPSecProxyIDSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = IPSecProxyIDFilterSet
    ordering_fields = ["tunnel__name", "local_subnet", "remote_subnet", "protocol"]
    search_fields = ["local_subnet", "remote_subnet", "protocol"]
    pagination_class = StandardResultsSetPagination


# -----------------------------
# VPN TOPOLOGY (UPDATED ONLY)
# -----------------------------


def latlon_to_xy(lat, lon, svg_width=2754, svg_height=1398):
    """Map latitude and longitude to SVG x, y coordinates (equirectangular)."""
    x = (lon + 180) * (svg_width / 360.0)
    y = (90 - lat) * (svg_height / 180.0)
    return x, y


def _neo4j_driver():
    """Create a Neo4j driver based on settings."""
    return GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))


class VPNTopologyNeo4jView(APIView):
    """
    Returns GeoJSON for MapLibre:

    {
      "devices": FeatureCollection(Point),
      "tunnels": FeatureCollection(LineString),
      "stats": { "active": N, "failed": M, "planned": K, ... },
      "meta":  {
        "devices_count": int,
        "tunnels_count": int,
        "countries_count": int,
        "platforms_count": int,
        "ha_pairs": int,
        "last_synced": ISO8601 or null
      }
    }
    """

    serializer_class = DummySerializer
    permission_classes = [IsAuthenticated]

    def _build_node_where(self, params_in, qp_out):
        where = []
        if params_in.get("country"):
            where.append("toLower(n.country) = toLower($country)")
            qp_out["country"] = params_in["country"]

        if params_in.get("platform"):
            where.append("toLower(n.platform_name) CONTAINS toLower($platform)")
            qp_out["platform"] = params_in["platform"]

        if params_in.get("location"):
            where.append("toLower(n.location_name) CONTAINS toLower($location)")
            qp_out["location"] = params_in["location"]

        if params_in.get("device"):
            val = str(params_in["device"]).strip()
            # Guard against null lists with coalesce()
            where.append(
                "("
                "toLower($device_name) IN [dev IN coalesce(n.device_names, []) | toLower(dev)] "
                "OR $device_name IN coalesce(n.nautobot_device_pks, []) "
                "OR toLower(n.label) CONTAINS toLower($device_name)"
                ")"
            )
            qp_out["device_name"] = val

        if params_in.get("role"):
            where.append("toLower(n.role) = toLower($node_role)")
            qp_out["node_role"] = params_in["role"]

        return where

    def _build_edge_filter(self, params_in, qp_out):
        conds = []
        if params_in.get("status"):
            conds.append("toLower(r.status) = toLower($tunnel_status)")
            qp_out["tunnel_status"] = params_in["status"]

        if params_in.get("ike_version"):
            conds.append("toLower(r.ike_version) = toLower($ike_version)")
            qp_out["ike_version"] = params_in["ike_version"]

        if params_in.get("role"):
            conds.append("toLower(r.role) = toLower($tunnel_role)")
            qp_out["tunnel_role"] = params_in["role"]

        return conds

    def get(self, request):
        logger.info("Neo4j VPN Topology GET request from user %s with filters: %s", request.user, request.GET.dict())

        # Settings check
        for attr in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"):
            if not hasattr(settings, attr):
                logger.error("Neo4j connection settings are not fully configured in Nautobot settings.")
                return Response({"error": "Graph database service is not configured."}, status=503)

        driver = None
        try:
            driver = _neo4j_driver()
            driver.verify_connectivity()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Failed to connect to Neo4j for topology view: %s", exc, exc_info=True)
            return Response({"error": "Could not connect to graph database."}, status=503)

        params_in = request.GET.dict()

        # --- Relational statistics for ribbon summary ---
        tracked_status = [
            ("active", "Active"),
            ("down", "Down"),
            ("decommissioned", "Decommissioned"),
            ("disabled", "Disabled"),
            ("planned", "Planned"),
        ]
        status_counts = {slug: 0 for slug, _ in tracked_status}
        status_labels = {slug: label for slug, label in tracked_status}
        status_order = [slug for slug, _ in tracked_status]

        role_labels = {
            "primary": "Primary",
            "secondary": "Secondary",
            "tertiary": "Tertiary",
            "unassigned": "Unassigned",
        }
        role_counts = {key: 0 for key in role_labels}
        role_order = ["primary", "secondary", "tertiary"]
        total_tunnels = 0

        try:
            tunnels_qs = IPSECTunnel.objects.restrict(request.user, "view")

            status_filter = (params_in.get("status") or "").strip()
            role_filter = (params_in.get("role") or "").strip()

            Status = apps.get_model("extras", "Status")
            status_fields = {f.name for f in Status._meta.get_fields()}
            has_status_slug = "slug" in status_fields

            if status_filter:
                status_lookup = Q(status__name__iexact=status_filter)
                if has_status_slug:
                    status_lookup |= Q(status__slug__iexact=status_filter)
                tunnels_qs = tunnels_qs.filter(status_lookup)

            if role_filter:
                tunnels_qs = tunnels_qs.filter(role__iexact=role_filter)

            status_value_fields = ["status__name"]
            if has_status_slug:
                status_value_fields.append("status__slug")

            for row in tunnels_qs.values(*status_value_fields).annotate(total=Count("id")):
                status_name = (row.get("status__name") or "").strip()
                raw_key = row.get("status__slug") if has_status_slug else status_name
                slug_key = (raw_key or status_name or "unknown").strip().lower().replace(" ", "-")
                if not slug_key:
                    slug_key = "unknown"
                status_counts[slug_key] = row["total"]
                status_labels[slug_key] = status_name or status_labels.get(slug_key, slug_key.title())
                if slug_key not in status_order:
                    status_order.append(slug_key)

            for row in tunnels_qs.values("role").annotate(total=Count("id")):
                role_value = (row["role"] or "unassigned").lower()
                role_counts[role_value] = row["total"]
                if role_value not in role_order:
                    role_order.append(role_value)

            total_tunnels = tunnels_qs.count()
        except Exception as agg_exc:  # noqa: BLE001
            logger.error("Failed to compute relational tunnel statistics: %s", agg_exc, exc_info=True)

        qp = {}

        node_where = self._build_node_where(params_in, qp)
        node_query = "MATCH (n:VPNNode)"
        if node_where:
            node_query += " WHERE " + " AND ".join(node_where)
        node_query += " RETURN n"

        try:
            devices_fc = {"type": "FeatureCollection", "features": []}
            tunnels_fc = {"type": "FeatureCollection", "features": []}

            with driver.session(database=getattr(settings, "NEO4J_DATABASE", "neo4j")) as session:
                # ---- Nodes
                logger.debug("Node query: %s params=%s", node_query, qp)
                node_records = session.run(node_query, qp)

                node_ids = set()
                for rec in node_records:
                    nprops = dict(rec["n"])
                    node_id = nprops.get("id")
                    if not node_id:
                        continue
                    # accept several possible coord keys
                    lat = nprops.get("lat", nprops.get("latitude"))
                    lon = nprops.get("lon", nprops.get("longitude"))
                    if lat is None or lon is None:
                        # skip nodes without geo
                        continue

                    node_ids.add(node_id)
                    props = {
                        "id": node_id,
                        "name": nprops.get("name") or nprops.get("label") or "",
                        "status": nprops.get("status") or "unknown",
                        "role": nprops.get("role"),
                        "platform": nprops.get("platform_name"),
                        "country": nprops.get("country"),
                        "location": nprops.get("location_name"),
                        "is_ha_pair": bool(nprops.get("is_ha_pair")),
                        # Include backing device info to make device filter work with HA groups
                        "device_names": nprops.get("device_names") or [],
                        "nautobot_device_pks": nprops.get("nautobot_device_pks") or [],
                        "search_text": " ".join(
                            str(x)
                            for x in [
                                nprops.get("name") or nprops.get("label"),
                                nprops.get("role"),
                                nprops.get("platform_name"),
                                nprops.get("country"),
                                nprops.get("location_name"),
                            ]
                            if x
                        ),
                    }

                    devices_fc["features"].append(
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                            "properties": props,
                        }
                    )

                # ---- Edges (include peers even if they don't match the node filters) ----
                edge_qp = {}
                edge_conds = self._build_edge_filter(params_in, edge_qp)

                base = (
                    "MATCH (a:VPNNode)-[r:TUNNEL]->(b:VPNNode) "
                    "WHERE a.lat IS NOT NULL AND a.lon IS NOT NULL AND b.lat IS NOT NULL AND b.lon IS NOT NULL "
                )
                if node_ids:
                    base += "AND (a.id IN $node_ids OR b.id IN $node_ids) "
                    edge_qp["node_ids"] = list(node_ids)
                if edge_conds:
                    base += "AND " + " AND ".join(edge_conds) + " "
                edge_query = base + "RETURN a AS a, b AS b, r AS r"

                logger.debug("Edge query: %s params=%s", edge_query, edge_qp)
                nodes_map = {f["properties"]["id"]: f for f in devices_fc["features"]}
                for rec in session.run(edge_query, edge_qp):
                    aprops = dict(rec["a"])  # node a properties
                    bprops = dict(rec["b"])  # node b properties
                    rprops = dict(rec["r"])  # relationship properties

                    # Ensure endpoints exist in devices_fc
                    for np in (aprops, bprops):
                        nid = np.get("id")
                        if not nid or nid in nodes_map:
                            continue
                        lat = np.get("lat")
                        if lat is None:
                            lat = np.get("latitude")
                        lon = np.get("lon")
                        if lon is None:
                            lon = np.get("longitude")
                        if lat is None or lon is None:
                            continue
                        props = {
                            "id": nid,
                            "name": np.get("name") or np.get("label") or "",
                            "status": np.get("status") or "unknown",
                            "role": np.get("role"),
                            "platform": np.get("platform_name"),
                            "country": np.get("country"),
                            "location": np.get("location_name"),
                            "is_ha_pair": bool(np.get("is_ha_pair")),
                            "device_names": np.get("device_names") or [],
                            "nautobot_device_pks": np.get("nautobot_device_pks") or [],
                            "search_text": " ".join(
                                str(x)
                                for x in [
                                    np.get("name") or np.get("label"),
                                    np.get("role"),
                                    np.get("platform_name"),
                                    np.get("country"),
                                    np.get("location_name"),
                                ]
                                if x
                            ),
                        }
                        feat = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [float(lon), float(lat)],
                            },
                            "properties": props,
                        }
                        devices_fc["features"].append(feat)
                        nodes_map[nid] = feat

                    # Add tunnel feature
                    a_lon = aprops.get("lon") if aprops.get("lon") is not None else aprops.get("longitude")
                    a_lat = aprops.get("lat") if aprops.get("lat") is not None else aprops.get("latitude")
                    b_lon = bprops.get("lon") if bprops.get("lon") is not None else bprops.get("longitude")
                    b_lat = bprops.get("lat") if bprops.get("lat") is not None else bprops.get("latitude")
                    if a_lon is None or a_lat is None or b_lon is None or b_lat is None:
                        continue
                    tunnels_fc["features"].append(
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [float(a_lon), float(a_lat)],
                                    [float(b_lon), float(b_lat)],
                                ],
                            },
                            "properties": {
                                "name": rprops.get("label") or rprops.get("id") or "",
                                "status": rprops.get("status") or "unknown",
                                "role": rprops.get("role") or "",
                                "ike_version": rprops.get("ike_version") or "",
                                "scope": rprops.get("scope") or "",
                                "local_ip": rprops.get("local_ip") or "",
                                "peer_ip": rprops.get("peer_ip") or "",
                                "firewall_hostnames": rprops.get("firewall_hostnames") or "",
                                "tooltip": rprops.get("tooltip_details_json") or rprops.get("tooltip") or "",
                            },
                        }
                    )

            # ---- Stats (by device status) ----
            stats = {}
            for f in devices_fc["features"]:
                s = (f["properties"].get("status") or "unknown").lower()
                stats[s] = stats.get(s, 0) + 1

            # ---- Meta for ribbon ----
            countries = set()
            platforms = set()
            ha_pairs = 0
            for f in devices_fc["features"]:
                p = f["properties"] or {}
                if p.get("country"):
                    countries.add(p["country"])
                if p.get("platform"):
                    platforms.add(p["platform"])
                if p.get("is_ha_pair"):
                    ha_pairs += 1

            last_synced_iso = None
            last_sync_status = None
            try:
                dash = VPNDashboard.objects.filter(pk=1).only("last_sync_time", "last_sync_status").first()
                if dash and dash.last_sync_time:
                    last_synced_iso = dash.last_sync_time.isoformat()
                if dash and dash.last_sync_status:
                    last_sync_status = dash.last_sync_status
            except Exception:  # noqa: BLE001
                pass

            meta = {
                "devices_count": len(devices_fc["features"]),
                "tunnels_count": len(tunnels_fc["features"]),
                "countries_count": len(countries),
                "platforms_count": len(platforms),
                "ha_pairs": ha_pairs,
                "last_synced": last_synced_iso,
                "last_sync_status": last_sync_status,
                "status_counts": status_counts,
                "status_labels": status_labels,
                "status_order": status_order,
                "role_counts": role_counts,
                "role_labels": role_labels,
                "role_order": role_order,
                "total_tunnels": total_tunnels,
                "total_primary_tunnels": role_counts.get("primary", 0),
                "total_secondary_tunnels": role_counts.get("secondary", 0),
                "total_tertiary_tunnels": role_counts.get("tertiary", 0),
                "total_unassigned_tunnels": role_counts.get("unassigned", 0),
            }

            return Response({"devices": devices_fc, "tunnels": tunnels_fc, "stats": stats, "meta": meta})

        except neo4j_exceptions.CypherSyntaxError as e:  # pylint: disable=broad-exception-caught
            logger.error("Neo4j Cypher Syntax Error in VPNTopologyNeo4jView: %s", e, exc_info=True)
            return Response({"error": "Error querying graph database (query syntax problem)."}, status=500)
        except neo4j_exceptions.ServiceUnavailable:
            logger.error("Neo4j Service Unavailable during VPN topology query.", exc_info=True)
            return Response({"error": "Graph database service unavailable during query."}, status=503)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error querying or processing data from Neo4j in VPNTopologyNeo4jView: %s", exc, exc_info=True)
            return Response({"error": "Could not retrieve topology data from graph database."}, status=500)
        finally:
            if driver:
                driver.close()


class VPNTopologyFilterOptionsView(APIView):
    """
    Returns arrays per filter key your UI expects:
    {
      "country": [...], "role": [...], "status": [...],
      "ike_version": [...], "location": [...],
      "device": [...], "platform": [...]
    }
    (Built from relational data; no change to IKE/IPSec logic.)
    """

    serializer_class = DummySerializer
    permission_classes = [IsAuthenticated]

    def _get_device_country_from_name(self, device_name):
        """Derives country from device name based on 'CODE-...' convention."""
        if device_name:
            parts = device_name.split("-")
            if parts:
                return parts[0].upper()
        return None

    def get(self, request):
        logger.debug("Filter options GET request from user %s", request.user)
        countries = set()
        ike_versions = set()
        statuses = set()
        tunnel_roles = set()
        devices = set()
        locations = set()
        platforms = set()

        tunnels_qs = IPSECTunnel.objects.select_related(
            "ike_gateway", "status", "ike_gateway__local_platform", "ike_gateway__peer_platform"
        ).prefetch_related(
            "ike_gateway__local_devices__platform",
            "ike_gateway__local_devices__location",
            "ike_gateway__local_devices__role",
            "ike_gateway__peer_devices__platform",
            "ike_gateway__peer_devices__location",
            "ike_gateway__peer_devices__role",
        )

        for tunnel in tunnels_qs:
            if tunnel.status and tunnel.status.name:
                statuses.add(tunnel.status.name)
            if tunnel.role:
                tunnel_roles.add(str(tunnel.role))

            gw = tunnel.ike_gateway
            if gw:
                if gw.ike_version:
                    ike_versions.add(str(gw.ike_version))

                for dev_group in [gw.local_devices.all(), gw.peer_devices.all()]:
                    for dev in dev_group:
                        if dev and dev.name:
                            devices.add(dev.name)
                            country = self._get_device_country_from_name(dev.name)
                            if country:
                                countries.add(country)
                        if dev and dev.location and dev.location.name:
                            locations.add(dev.location.name)
                        if dev and dev.platform and dev.platform.name:
                            platforms.add(dev.platform.name)

                # consider local/peer platforms on gateway
                for plat in [gw.local_platform, gw.peer_platform]:
                    if plat and plat.name:
                        platforms.add(plat.name)

        # also include all defined platforms
        for plat in Platform.objects.all().values("name").distinct():
            if plat["name"]:
                platforms.add(plat["name"])

        # OUTPUT KEYS match frontend expectations
        return Response(
            {
                "country": sorted(filter(None, countries)),
                "ike_version": sorted(filter(None, ike_versions)),
                "status": sorted(filter(None, statuses)),
                "role": sorted(filter(None, tunnel_roles)),
                "location": sorted(filter(None, locations)),
                "device": sorted(filter(None, devices)),
                "platform": sorted(filter(None, platforms)),
            }
        )
