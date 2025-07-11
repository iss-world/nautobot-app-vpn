"""API viewsets for the Nautobot VPN plugin."""
# pylint: disable=too-many-ancestors, too-many-locals, too-many-branches, too-many-statements, too-many-nested-blocks

import logging
import random
from django.conf import settings
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

logger = logging.getLogger(__name__)


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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]  # Uncommented filter_backends
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
            "bind_interface",  # Added bind_interface
        )
        .prefetch_related("local_devices", "peer_devices", "local_locations", "peer_locations")
        .order_by("name")
    )

    serializer_class = IKEGatewaySerializer  # Use updated serializer
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
        """Create a new VPN object via API."""
        serializer.save()

    def perform_update(self, serializer):
        """Update a new VPN object via API."""
        serializer.save()


class TunnelMonitorProfileViewSet(viewsets.ModelViewSet):
    """API viewset for Tunnel Monitor Profiles."""

    queryset = TunnelMonitorProfile.objects.all().order_by("name")
    serializer_class = TunnelMonitorProfileSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]  # Uncommented filter_backends
    filterset_class = TunnelMonitorProfileFilterSet
    ordering_fields = ["name", "action", "interval", "threshold"]
    search_fields = ["name"]
    pagination_class = StandardResultsSetPagination


class IPSECTunnelViewSet(viewsets.ModelViewSet):
    """API viewset for IPSec Tunnels."""

    # <<< UPDATED queryset: Removed bind_interface from select_related >>>
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
        """Create a new VPN object via API."""
        serializer.save()

    def perform_update(self, serializer):
        """Update a new VPN object via API."""
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


def latlon_to_xy(lat, lon, svg_width=2754, svg_height=1398):
    """Map latitude and longitude to SVG x, y coordinates.
    Assumes equirectangular projection.
    """
    x = (lon + 180) * (svg_width / 360.0)
    y = (90 - lat) * (svg_height / 180.0)
    return x, y


class VPNTopologyNeo4jView(APIView):
    """API view to return VPN topology nodes and edges for visualization,
    sourced from Neo4j, with support for filtering.
    """

    serializer_class = DummySerializer
    permission_classes = [IsAuthenticated]

    def _build_cypher_queries_and_params(self, filters_dict):
        """Builds Cypher queries and parameters for fetching nodes and edges based on request filters.
        Returns: (nodes_query_string, edges_query_string, query_parameters_dict)
        """
        query_params = {}

        node_match_clause = "MATCH (n:VPNNode)"
        node_where_clauses = []

        if filters_dict.get("country"):
            node_where_clauses.append("toLower(n.country) = toLower($country)")
            query_params["country"] = filters_dict["country"]

        if filters_dict.get("platform"):
            platform_val = filters_dict["platform"]
            node_where_clauses.append("toLower(n.platform_name) CONTAINS toLower($platform)")
            query_params["platform"] = platform_val

        if filters_dict.get("location"):
            node_where_clauses.append("toLower(n.location_name) CONTAINS toLower($location)")
            query_params["location"] = filters_dict["location"]

        if filters_dict.get("device"):
            val = str(filters_dict["device"]).strip()
            node_where_clauses.append(
                "("
                "toLower($device_name) IN [dev IN n.device_names | toLower(dev)] "
                "OR $device_name IN n.nautobot_device_pks "
                "OR toLower(n.label) CONTAINS toLower($device_name)"
                ")"
            )
            query_params["device_name"] = val

        if filters_dict.get("role"):
            node_where_clauses.append("toLower(n.role) = toLower($device_role)")
            query_params["device_role"] = filters_dict["role"]

        nodes_query_string = node_match_clause
        if node_where_clauses:
            nodes_query_string += " WHERE " + " AND ".join(node_where_clauses)
        nodes_query_string += " RETURN n"

        edges_query_string = (
            "MATCH (n1:VPNNode)-[r:TUNNEL]->(n2:VPNNode) WHERE n1.id IN $node_ids AND n2.id IN $node_ids"
        )
        edge_filter_conditions = []

        if filters_dict.get("status"):
            edge_filter_conditions.append("toLower(r.status) = toLower($tunnel_status)")
            query_params["tunnel_status"] = filters_dict["status"]

        if filters_dict.get("ike_version"):
            edge_filter_conditions.append("toLower(r.ike_version) = toLower($ike_version)")
            query_params["ike_version"] = filters_dict["ike_version"]

        if filters_dict.get("role"):  # Use "role" consistently
            edge_filter_conditions.append("toLower(r.role) = toLower($tunnel_role)")
            query_params["tunnel_role"] = filters_dict["role"]

        if edge_filter_conditions:
            edges_query_string += " AND " + " AND ".join(edge_filter_conditions)

        edges_query_string += " RETURN n1.id AS source, n2.id AS target, r AS properties"

        return nodes_query_string, edges_query_string, query_params

    def get(self, request):
        """Handle GET request for available VPN topology filter options."""
        logger.info("Neo4j VPN Topology GET request from user %s with filters: %s", request.user, request.GET.dict())

        if not all(hasattr(settings, attr) for attr in ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]):
            logger.error("Neo4j connection settings are not fully configured in Nautobot settings.")
            return Response({"error": "Graph database service is not configured."}, status=503)

        driver = None
        try:
            driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
            driver.verify_connectivity()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Failed to connect to Neo4j for topology view: %s", exc, exc_info=True)
            return Response({"error": "Could not connect to graph database."}, status=503)

        formatted_nodes = []
        formatted_edges = []

        request_filters = request.GET.dict()
        nodes_cypher, edges_cypher, query_params_base = self._build_cypher_queries_and_params(request_filters)  # pylint: disable=unused-variable

        try:
            with driver.session(database=getattr(settings, "NEO4J_DATABASE", "neo4j")) as session:
                logger.debug("Executing Neo4j Node Query: %s with params: %s", nodes_cypher, query_params_base)
                node_records = session.run(nodes_cypher, query_params_base)
                focus_node_ids = set()
                temp_nodes_dict = {}

                for record in node_records:
                    node_data_neo = record["n"]
                    node_properties = dict(node_data_neo)
                    node_id = node_properties.get("id")
                    if node_id:
                        focus_node_ids.add(node_id)
                        if node_id not in temp_nodes_dict:
                            lat = node_properties.get("latitude")
                            lon = node_properties.get("longitude")
                            x = node_properties.get("x")
                            y = node_properties.get("y")
                            pos = None

                            if x is not None and y is not None:
                                try:
                                    pos = {"x": float(x), "y": float(y)}
                                except Exception:  # pylint: disable=broad-exception-caught
                                    pos = None
                            elif lat is not None and lon is not None:
                                try:
                                    x_map, y_map = latlon_to_xy(float(lat), float(lon), svg_width=2754, svg_height=1398)
                                    pos = {"x": x_map, "y": y_map}
                                except Exception:  # pylint: disable=broad-exception-caught
                                    pos = {"x": random.uniform(-100, 100), "y": random.uniform(-100, 100)}
                            else:
                                pos = {"x": random.uniform(-100, 100), "y": random.uniform(-100, 100)}

                            node_obj = {
                                "data": {
                                    **node_properties,
                                    "is_ha_pair": node_properties.get("is_ha_pair", False),
                                    "node_type": node_properties.get("node_type", "DeviceGroup"),
                                    "label": node_properties.get("label", ""),
                                }
                            }
                            if pos:
                                node_obj["position"] = pos
                            temp_nodes_dict[node_id] = node_obj

                if focus_node_ids:
                    edge_query = """
                        MATCH (n1:VPNNode)-[r:TUNNEL]->(n2:VPNNode)
                        WHERE n1.id IN $focus_node_ids OR n2.id IN $focus_node_ids
                        RETURN n1.id AS source, n2.id AS target, r AS properties
                    """
                    logger.debug("Executing Neo4j Edge Query: %s with focus_node_ids: %s", edge_query, focus_node_ids)
                    edge_records = session.run(edge_query, {"focus_node_ids": list(focus_node_ids)})

                    all_node_ids = set(focus_node_ids)  # Start with focus nodes

                    for record in edge_records:
                        source_id = record["source"]
                        target_id = record["target"]
                        all_node_ids.add(source_id)
                        all_node_ids.add(target_id)

                        edge_rel_properties = dict(record["properties"])
                        if "nautobot_tunnel_pk" in edge_rel_properties:
                            edge_rel_properties["id"] = f"tunnel_{edge_rel_properties['nautobot_tunnel_pk']}"
                        else:
                            edge_rel_properties["id"] = f"edge_{record['properties'].element_id}"

                        edge_rel_properties["tooltip_details"] = {
                            "Tunnel Name": edge_rel_properties.get("name", "N/A"),
                            "Status": edge_rel_properties.get("status", "N/A"),
                            "Role": edge_rel_properties.get("role", "N/A"),
                            "IKE Gateway": edge_rel_properties.get("ike_gateway_name", "N/A"),
                            "IKE Version": edge_rel_properties.get("ike_version", "N/A"),
                            "IPsec Profile": edge_rel_properties.get("ipsec_profile_name", "N/A"),
                            "Tunnel Interface": edge_rel_properties.get("tunnel_interface", "N/A"),
                            "Description": edge_rel_properties.get("description", ""),
                        }

                        formatted_edges.append(
                            {
                                "data": {
                                    "source": source_id,
                                    "target": target_id,
                                    **edge_rel_properties,
                                    "label": edge_rel_properties.get("label", edge_rel_properties.get("name", "")),
                                }
                            }
                        )

                    if all_node_ids:
                        all_nodes_query = "MATCH (n:VPNNode) WHERE n.id IN $all_node_ids RETURN n"
                        all_nodes_records = session.run(all_nodes_query, {"all_node_ids": list(all_node_ids)})
                        for record in all_nodes_records:
                            node_data_neo = record["n"]
                            node_properties = dict(node_data_neo)
                            node_id = node_properties.get("id")
                            if node_id and node_id not in temp_nodes_dict:
                                lat = node_properties.get("latitude")
                                lon = node_properties.get("longitude")
                                x = node_properties.get("x")
                                y = node_properties.get("y")
                                pos = None

                                if x is not None and y is not None:
                                    try:
                                        pos = {"x": float(x), "y": float(y)}
                                    except Exception:  # pylint: disable=broad-exception-caught
                                        pos = None
                                elif lat is not None and lon is not None:
                                    try:
                                        x_map, y_map = latlon_to_xy(
                                            float(lat), float(lon), svg_width=2754, svg_height=1398
                                        )
                                        pos = {"x": x_map, "y": y_map}
                                    except Exception:  # pylint: disable=broad-exception-caught
                                        pos = {"x": random.uniform(-100, 100), "y": random.uniform(-100, 100)}
                                else:
                                    pos = {"x": random.uniform(-100, 100), "y": random.uniform(-100, 100)}

                                node_obj = {
                                    "data": {
                                        **node_properties,
                                        "is_ha_pair": node_properties.get("is_ha_pair", False),
                                        "node_type": node_properties.get("node_type", "DeviceGroup"),
                                        "label": node_properties.get("label", ""),
                                    }
                                }
                                if pos:
                                    node_obj["position"] = pos
                                temp_nodes_dict[node_id] = node_obj

                formatted_nodes = list(temp_nodes_dict.values())

            graph_data_response = {
                "nodes": formatted_nodes,
                "edges": formatted_edges,
                "meta": {
                    "total_nodes_shown": len(formatted_nodes),
                    "total_edges_shown": len(formatted_edges),
                    "active_tunnels_shown": sum(
                        1 for e in formatted_edges if e["data"].get("status", "").lower() == "active"
                    ),
                    "failed_tunnels_shown": sum(
                        1 for e in formatted_edges if e["data"].get("status", "").lower() in ["failed", "down"]
                    ),
                    "planned_tunnels_shown": sum(
                        1 for e in formatted_edges if e["data"].get("status", "").lower() == "planned"
                    ),
                    "ha_pairs_shown": sum(1 for n in formatted_nodes if n["data"].get("is_ha_pair", False)),
                    "focus_node_ids": list(focus_node_ids),
                },
            }

            try:
                dashboard = VPNDashboard.objects.order_by("-last_sync_time").first()
                if dashboard:
                    graph_data_response["meta"]["last_synced_at"] = (
                        dashboard.last_sync_time.isoformat() if dashboard.last_sync_time else None
                    )
                    graph_data_response["meta"]["last_sync_status"] = dashboard.last_sync_status
                else:
                    graph_data_response["meta"]["last_synced_at"] = None
                    graph_data_response["meta"]["last_sync_status"] = "Unknown (No Dashboard Data)"
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to read VPNDashboard for sync time: %s", exc, exc_info=True)
                graph_data_response["meta"]["last_synced_at"] = None
                graph_data_response["meta"]["last_sync_status"] = "Error reading status"

            return Response(graph_data_response)

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
    """API view to return distinct filter options for countries, platforms, roles, etc.,
    primarily based on data currently associated with IPSECTunnels in Nautobot's relational DB.
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
        """Handle GET request for available VPN filter options."""
        logger.debug("Filter options GET request from user %s", request.user)
        countries = set()
        ike_versions = set()
        statuses = set()
        tunnel_roles = set()
        devices_map = {}
        locations = set()
        platforms_set = set()  # store (id, name)

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

                for plat in [gw.local_platform, gw.peer_platform]:
                    if plat:
                        platforms_set.add((plat.id, plat.name))

                for dev_group in [gw.local_devices.all(), gw.peer_devices.all()]:
                    for dev in dev_group:
                        if dev and dev.name:
                            devices_map[str(dev.pk)] = dev.name
                            country = self._get_device_country_from_name(dev.name)
                            if country:
                                countries.add(country)
                        if dev and dev.location and dev.location.name:
                            locations.add(dev.location.name)
                        if dev and dev.platform:
                            platforms_set.add((dev.platform.id, dev.platform.name))

        all_defined_platforms = Platform.objects.all().values("id", "name").distinct()
        for plat in all_defined_platforms:
            platforms_set.add((plat["id"], plat["name"]))

        platforms_out = [
            {"id": pid, "name": n} for pid, n in sorted(platforms_set, key=lambda x: (x[1] or "", x[0] or "")) if n
        ]

        return Response(
            {
                "countries": sorted(filter(None, countries)),
                "ike_versions": sorted(filter(None, ike_versions)),
                "statuses": sorted(filter(None, statuses)),
                "roles": sorted(filter(None, tunnel_roles)),
                "tunnel_roles": sorted(filter(None, tunnel_roles)),
                "devices": [
                    {"id": pk, "label": name} for pk, name in sorted(devices_map.items(), key=lambda item: item[1])
                ],
                "locations": sorted(filter(None, locations)),
                "platforms": platforms_out,
            }
        )
