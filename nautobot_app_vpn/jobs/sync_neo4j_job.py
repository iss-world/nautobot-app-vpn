"""Job to synchronize VPN topology into Neo4j."""
# pylint: disable=too-many-statements, too-many-branches, too-many-locals, too-few-public-methods
# noqa: PLR0915, PLR0912, PLR0914
# pylint: disable=broad-exception-caught

import json
import logging
import random
import re
from datetime import UTC, datetime
from ipaddress import ip_address, ip_interface

from django.conf import settings
from django.db.models import Prefetch
from nautobot.dcim.models import Device
from nautobot.extras.jobs import Job
from neo4j import GraphDatabase
from neo4j import exceptions as neo4j_exceptions

# ✅ Nautobot IPAM model uses `host` + `mask_length` (not `address`)
from nautobot.ipam.models import IPAddress

from nautobot_app_vpn.models import IKEGateway, IPSECTunnel, VPNDashboard

logger = logging.getLogger(__name__)  # Module-level logger

name = "Virtual Private Network (VPN)"  # pylint: disable=invalid-name


class SyncNeo4jJob(Job):
    """Job to sync VPN topology to Neo4j."""

    class Meta:
        name = "Sync VPN Topology to Neo4j"
        description = "Pushes VPN device/tunnel relationships to Neo4j for graph visualization."

    # Fallback coordinates by country code for when lat/long is not available
    FALLBACK_COORDS_BY_COUNTRY = {
        "SG": (1.3521, 103.8198),
        "UK": (51.5074, -0.1278),
        "US": (38.8951, -77.0364),
        "DE": (52.52, 13.4050),
        "FR": (48.8566, 2.3522),
        "IN": (28.6139, 77.2090),
        "AU": (-33.8688, 151.2093),
        "CN": (39.9042, 116.4074),
        "ES": (40.4168, -3.7038),
        "IT": (41.9028, 12.4964),
        "NL": (52.3676, 4.9041),
        "SE": (59.3293, 18.0686),
        "PL": (52.2297, 21.0122),
        "MX": (19.4326, -99.1332),
        "ID": (-6.2088, 106.8456),
        "BE": (50.8503, 4.3517),
        "IE": (53.3498, -6.2603),
        "CH": (46.9481, 7.4474),
        "FI": (60.1695, 24.9354),
        "LT": (54.6872, 25.2797),
        "TR": (39.9208, 32.8541),
        "NO": (59.9139, 10.7522),
        "NZ": (-41.2865, 174.7762),
        "DK": (55.6761, 12.5683),
        "CL": (-33.4489, -70.6693),
        "AT": (48.2082, 16.3738),
        "JP": (35.6762, 139.6503),
        "KR": (37.5665, 126.9780),
        "BR": (-15.7801, -47.9292),
        "CA": (45.4215, -75.6972),
        "RU": (55.7558, 37.6173),
        "ZA": (-33.9249, 18.4241),
        "AE": (25.2048, 55.2708),
        "SA": (24.7136, 46.6753),
        "TH": (13.7563, 100.5018),
        "MY": (3.1390, 101.6869),
        "VN": (21.0285, 105.8542),
        "PH": (14.5995, 120.9842),
        "HK": (22.3193, 114.1694),
        "TW": (25.0330, 121.5654),
        # Add others as needed
    }

    def get_fallback_coords_by_country(self, country_code):
        """Get fallback (latitude, longitude) for a given country code."""
        base_coords = self.FALLBACK_COORDS_BY_COUNTRY.get((country_code or "UN").upper())
        if base_coords:
            lat_offset = random.uniform(-0.5, 0.5)
            lon_offset = random.uniform(-0.5, 0.5)
            return (base_coords[0] + lat_offset, base_coords[1] + lon_offset)
        return (random.uniform(-50, 50), random.uniform(-180, 180))

    def run(self, *args, **kwargs):
        """Main job execution logic."""

        has_logger_failure = hasattr(self.logger, "failure")
        has_logger_success = hasattr(self.logger, "success")

        def log_job_failure(message):
            full_message = f"JOB_FAILURE: {message}"
            self.logger.failure(full_message) if has_logger_failure else self.logger.error(full_message)

        def log_job_success(message):
            full_message = f"JOB_SUCCESS: {message}"
            self.logger.success(full_message) if has_logger_success else self.logger.info(full_message)

        log_job_info = self.logger.info
        log_job_warning = self.logger.warning
        log_job_debug = self.logger.debug

        log_job_info("VPN Topology to Neo4j sync job started.")

        if not all(hasattr(settings, attr) for attr in ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]):
            msg = "Neo4j connection settings (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) are not configured in Nautobot settings."
            log_job_failure(msg)
            raise RuntimeError(msg)

        log_job_info("🔗 Connecting to Neo4j at %s...", settings.NEO4J_URI)
        driver = None
        try:
            driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
            driver.verify_connectivity()
            log_job_info("Successfully connected to Neo4j.")
        except neo4j_exceptions.ServiceUnavailable as e:
            msg = f"Failed to connect to Neo4j: Service Unavailable. {e}"
            log_job_failure(msg)
            if driver:
                driver.close()
            raise RuntimeError(msg) from e
        except neo4j_exceptions.AuthError as e:
            msg = f"Failed to connect to Neo4j: Authentication Error. {e}"
            log_job_failure(msg)
            if driver:
                driver.close()
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"Failed to connect to Neo4j: {e}"
            log_job_failure(msg)
            logger.error("Neo4j Connection Exception Details: %s", e, exc_info=True)
            if driver:
                driver.close()
            raise RuntimeError(msg) from e

        now_utc = datetime.now(UTC)
        processed_node_counts = {"DeviceGroup": 0, "ManualPeer": 0}
        edges_synced_count = 0

        # ---------- Build a fast IP index from DCIM device interface IPs ----------
        # We consider an IP "present" if it is assigned to any dcim.Interface. We store only the host, no prefix.
        ip_index: set[str] = set()
        try:
            # Nautobot 2.x uses M2M relations: `interfaces` and `vm_interfaces`.
            qs1 = IPAddress.objects.filter(interfaces__isnull=False).values_list("host", flat=True)
            qs2 = IPAddress.objects.filter(vm_interfaces__isnull=False).values_list("host", flat=True)
            for host in qs1.iterator():
                if host:
                    ip_index.add(str(host))
            for host in qs2.iterator():
                if host:
                    ip_index.add(str(host))
            log_job_info(
                "Preloaded %s interface IPs (device/vm interface assignments) for scope classification.",
                len(ip_index),
            )
        except Exception as e:
            log_job_warning("Unable to preload IP address index for scope classification: %s", e)

        def _host_only(ip_value):
            """Return just the host part of an IP string (CIDR or raw)."""
            if not ip_value:
                return ""
            s = str(ip_value).strip()
            try:
                if "/" in s:
                    return str(ip_interface(s).ip)
                return str(ip_address(s))
            except Exception:
                m = re.search(r"([0-9]{1,3}(?:\.[0-9]{1,3}){3})", s)
                return m.group(1) if m else s

        def classify_scope(local_ip, peer_ip, has_local_devices=False, has_peer_devices=False):
            """Classify a tunnel as 'internal' when both sides are known in Nautobot.

            A tunnel is considered internal when:
            * both local_ip and peer_ip are assigned to Nautobot interfaces, OR
            * both local and peer device groups contain at least one Nautobot Device.
            Everything else is treated as external.
            """
            try:
                li = _host_only(local_ip)
                pi = _host_only(peer_ip)
                if li and pi and (li in ip_index) and (pi in ip_index):
                    return "internal"
                if has_local_devices and has_peer_devices:
                    return "internal"
            except Exception:  # defensive
                pass
            return "external"

        try:
            with driver.session(database=getattr(settings, "NEO4J_DATABASE", "neo4j")) as session:
                log_job_info("🧹 Clearing existing VPNNode subgraph in Neo4j...")
                try:
                    session.execute_write(lambda tx: tx.run("MATCH (n:VPNNode) DETACH DELETE n"))
                    log_job_info("Successfully cleared VPNNode subgraph.")
                except Exception as exc:
                    msg = f"Failed to clear Neo4j subgraph: {exc}"
                    log_job_failure(msg)
                    logger.error("Neo4j Clear Subgraph Exception Details: %s", exc, exc_info=True)
                    raise RuntimeError(msg) from exc

                device_prefetch_qs = Device.objects.select_related(
                    "platform", "role", "location", "status", "device_type", "primary_ip4"
                ).prefetch_related("tags")

                tunnels_qs = IPSECTunnel.objects.select_related(
                    "ike_gateway",
                    "ike_gateway__status",
                    "ike_gateway__local_platform",
                    "ike_gateway__peer_platform",
                    "status",
                    "monitor_profile",
                    "tunnel_interface__device",
                    "ipsec_crypto_profile",
                ).prefetch_related(
                    Prefetch("ike_gateway__local_devices", queryset=device_prefetch_qs),
                    Prefetch("ike_gateway__peer_devices", queryset=device_prefetch_qs),
                    "proxy_ids",
                )

                neo4j_nodes_to_create = {}
                neo4j_edges_to_create = []

                def get_node_id(devices_list=None, manual_name=None):
                    if devices_list:
                        return f"group:{'|'.join(sorted(str(d.pk) for d in devices_list))}"
                    if manual_name:
                        return f"manual_peer:{manual_name.strip().replace(' ', '_').replace('/', '_').lower()}"
                    return None

                def get_node_label(devices_list=None, manual_name=None):
                    if devices_list:
                        return " <-> ".join(sorted(d.name for d in devices_list))
                    return manual_name or "Unknown Peer"

                def get_device_country(device_obj, manual_location_str=None):
                    if device_obj and device_obj.location and hasattr(device_obj.location, "custom_field_data"):
                        loc_cf = device_obj.location.custom_field_data
                        country = loc_cf.get("country_code") or loc_cf.get("country")
                        if country:
                            return str(country).upper()
                    if device_obj and device_obj.name:
                        parts = device_obj.name.split("-")
                        return parts[0].upper() if parts else "UN"
                    if manual_location_str:
                        parts = manual_location_str.split(",")
                        return (
                            parts[-1].strip().upper()
                            if len(parts) > 1
                            else (parts[0].strip().upper() if parts and parts[0].strip() else "UN")
                        )
                    return "UN"

                def sanitize_filename(input_name):
                    return re.sub(r"[^A-Za-z0-9_\-]", "_", input_name)

                for tunnel in tunnels_qs:
                    gw: IKEGateway = tunnel.ike_gateway
                    if not gw:
                        continue

                    local_devs_group = list(gw.local_devices.all())
                    if not local_devs_group:
                        continue

                    peer_devs_group = list(gw.peer_devices.all())

                    # ---------- Local node ----------
                    local_node_id_val = get_node_id(devices_list=local_devs_group)
                    if local_node_id_val and local_node_id_val not in neo4j_nodes_to_create:
                        dev = local_devs_group[0]
                        country_code = get_device_country(dev, None)

                        # final lat/lon
                        if dev.location and dev.location.latitude and dev.location.longitude:
                            lat = float(dev.location.latitude)
                            lon = float(dev.location.longitude)
                        else:
                            lat, lon = self.get_fallback_coords_by_country(country_code)

                        loc_name = dev.location.name if dev.location else "Unknown"
                        platform_obj = gw.local_platform if gw.local_platform else dev.platform
                        p_name = platform_obj.name if platform_obj else "Unknown"
                        icon_f = f"{sanitize_filename(p_name)}.svg" if p_name != "Unknown" else "unknown.svg"

                        # NOTE: write BOTH lat/lon and latitude/longitude to nodes
                        neo4j_nodes_to_create[local_node_id_val] = {
                            "id": local_node_id_val,
                            "label": get_node_label(devices_list=local_devs_group),
                            "node_type": "DeviceGroup",
                            "country": country_code,
                            "location_name": loc_name,
                            "latitude": lat,
                            "longitude": lon,
                            "lat": lat,
                            "lon": lon,
                            "x": lon,
                            "y": lat,
                            "platform_name": p_name,
                            "icon_filename": icon_f,
                            "status": dev.status.name if dev.status else "Unknown",
                            "role": dev.role.name if dev.role else "Unknown",
                            # ✅ Nautobot: primary_ip4.host
                            "primary_ip": str(getattr(dev.primary_ip4, "host", "")) if dev.primary_ip4 else "",
                            "is_ha_pair": len(local_devs_group) > 1,
                            "model_name": dev.device_type.model if dev.device_type else "N/A",
                            "nautobot_device_pks": [str(d.pk) for d in local_devs_group],
                            "device_names": [d.name for d in local_devs_group],
                        }
                        processed_node_counts["DeviceGroup"] += 1

                    # ---------- Peer node ----------
                    peer_node_id_val, peer_node_label_val = None, None

                    if peer_devs_group and len(peer_devs_group) > 0:
                        peer_node_id_val = get_node_id(devices_list=peer_devs_group)
                        peer_node_label_val = get_node_label(devices_list=peer_devs_group)
                        if peer_node_id_val and peer_node_id_val not in neo4j_nodes_to_create:
                            dev = peer_devs_group[0]
                            country_code = get_device_country(dev, None)
                            if dev.location and dev.location.latitude and dev.location.longitude:
                                lat = float(dev.location.latitude)
                                lon = float(dev.location.longitude)
                            else:
                                lat, lon = self.get_fallback_coords_by_country(country_code)
                            loc_name = dev.location.name if dev.location else "Unknown"
                            platform_obj = gw.peer_platform if gw.peer_platform else dev.platform
                            p_name = platform_obj.name if platform_obj else "Unknown"
                            icon_f = f"{sanitize_filename(p_name)}.svg" if p_name != "Unknown" else "unknown.svg"
                            neo4j_nodes_to_create[peer_node_id_val] = {
                                "id": peer_node_id_val,
                                "label": peer_node_label_val,
                                "node_type": "DeviceGroup",
                                "country": country_code,
                                "location_name": loc_name,
                                "latitude": lat,
                                "longitude": lon,
                                "lat": lat,
                                "lon": lon,
                                "platform_name": p_name,
                                "icon_filename": icon_f,
                                "status": dev.status.name if dev.status else "Unknown",
                                "role": dev.role.name if dev.role else "Unknown",
                                "primary_ip": str(getattr(dev.primary_ip4, "host", "")) if dev.primary_ip4 else "",
                                "is_ha_pair": len(peer_devs_group) > 1,
                                "model_name": dev.device_type.model if dev.device_type else "N/A",
                                "nautobot_device_pks": [str(d.pk) for d in peer_devs_group],
                                "device_names": [d.name for d in peer_devs_group],
                            }
                            processed_node_counts["DeviceGroup"] += 1

                    elif (gw.peer_device_manual and gw.peer_device_manual.strip()) or (
                        gw.peer_location_manual and gw.peer_location_manual.strip()
                    ):
                        manual_peer_label = (gw.peer_device_manual or gw.peer_location_manual).strip()
                        # normalized id uses spaces and slashes replacement (consistent with get_node_id)
                        peer_node_id_val = (
                            f"manual_peer:{manual_peer_label.strip().lower().replace(' ', '_').replace('/', '_')}"
                        )
                        icon_f = "unknown.svg"
                        if getattr(gw, "peer_platform", None) and getattr(gw.peer_platform, "name", None):
                            platform_name = gw.peer_platform.name.strip()
                            icon_f = (
                                f"{sanitize_filename(platform_name)}.svg"
                                if platform_name and platform_name.lower() != "unknown"
                                else "unknown.svg"
                            )

                        peer_node_label_val = manual_peer_label
                        if peer_node_id_val not in neo4j_nodes_to_create:
                            lat, lon = self.get_fallback_coords_by_country("UN")
                            neo4j_nodes_to_create[peer_node_id_val] = {
                                "id": peer_node_id_val,
                                "label": manual_peer_label,
                                "node_type": "DeviceGroup",
                                "country": "UN",
                                "location_name": gw.peer_location_manual or "",
                                "latitude": lat,
                                "longitude": lon,
                                "lat": lat,
                                "lon": lon,
                                "platform_name": getattr(getattr(gw, "peer_platform", None), "name", "Unknown")
                                or "Unknown",
                                "icon_filename": icon_f,
                                "status": "Manual",
                                "role": "External",
                                "primary_ip": str(gw.peer_ip or "") or "",
                                "is_manual_peer": True,
                                "model_name": "",
                                "nautobot_device_pks": [],
                                "device_names": [manual_peer_label],
                            }
                            processed_node_counts["ManualPeer"] += 1
                    else:
                        logger.warning("No peer devices/manual peer data for tunnel %s (%s)", tunnel.name, tunnel.pk)
                        continue

                    # ---------- Edge ----------
                    if local_node_id_val and peer_node_id_val:
                        edge_label = tunnel.name or f"Tunnel {tunnel.pk}"

                        local_ip_str = str(getattr(gw, "local_ip", "") or "")
                        peer_ip_str = str(getattr(gw, "peer_ip", "") or "")
                        scope_val = classify_scope(
                            local_ip_str,
                            peer_ip_str,
                            bool(local_devs_group),
                            bool(peer_devs_group),
                        )

                        tooltip_details = {
                            "Tunnel Name": tunnel.name or "N/A",
                            "Status": getattr(tunnel.status, "name", "Unknown") if tunnel.status else "Unknown",
                            "Role": str(getattr(tunnel, "role", "") or "") or "Unknown",
                            "IKE Gateway": getattr(gw, "name", "") or "N/A",
                            "IKE Version": str(getattr(gw, "ike_version", "") or "") or "Unknown",
                            "IPsec Profile": getattr(getattr(tunnel, "ipsec_crypto_profile", None), "name", None)
                            or "N/A",
                            "Tunnel Interface": getattr(getattr(tunnel, "tunnel_interface", None), "name", None)
                            or "N/A",
                            "Description": tunnel.description or "",
                            "Local IP": local_ip_str or "N/A",
                            "Peer IP": peer_ip_str or "N/A",
                            "Scope": scope_val,
                            "Last Synced": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "Firewalls": ", ".join(
                                [d.name for d in local_devs_group + peer_devs_group if d and getattr(d, "name", None)]
                            ),
                        }

                        edge_props = {
                            "id": f"tunnel_{tunnel.pk}",
                            "label": edge_label,
                            "nautobot_tunnel_pk": str(tunnel.pk),
                            "status": getattr(tunnel.status, "name", "Unknown") if tunnel.status else "Unknown",
                            "role": str(getattr(tunnel, "role", "") or "") or "Unknown",
                            "ike_gateway_name": getattr(gw, "name", "") or "N/A",
                            "ike_version": str(getattr(gw, "ike_version", "") or "") or "Unknown",
                            "ipsec_profile_name": getattr(getattr(tunnel, "ipsec_crypto_profile", None), "name", None)
                            or "N/A",
                            "tunnel_interface": getattr(getattr(tunnel, "tunnel_interface", None), "name", None)
                            or "N/A",
                            "description": tunnel.description or "",
                            "synced_at_utc": now_utc.isoformat(),
                            "local_ip": local_ip_str or "N/A",
                            "peer_ip": peer_ip_str or "N/A",
                            "scope": scope_val,  # ✅ for frontend color/filtering
                            "firewall_hostnames": ", ".join(
                                [d.name for d in local_devs_group + peer_devs_group if d and getattr(d, "name", None)]
                            ),
                            "tooltip_details_json": json.dumps(tooltip_details, ensure_ascii=False),
                            "tooltip": json.dumps(tooltip_details, ensure_ascii=False),  # ✅ convenience for frontend
                        }
                        for k, v in list(edge_props.items()):
                            if isinstance(v, dict):
                                edge_props[k] = json.dumps(v, ensure_ascii=False)

                        neo4j_edges_to_create.append(
                            {"source_id": local_node_id_val, "target_id": peer_node_id_val, "properties": edge_props}
                        )
                        edges_synced_count += 1

                # ---- Bulk upserts ----
                if neo4j_nodes_to_create:
                    log_job_info("Creating/updating %s VPNNodes in Neo4j...", len(neo4j_nodes_to_create))
                    node_payloads = list(neo4j_nodes_to_create.values())
                    session.execute_write(
                        lambda tx: tx.run(
                            """
                            UNWIND $nodes_batch AS node_props
                            MERGE (n:VPNNode {id: node_props.id})
                            SET n = node_props
                            """,
                            {"nodes_batch": node_payloads},
                        )
                    )
                    log_job_debug("Processed %s nodes for Neo4j.", len(node_payloads))

                if neo4j_edges_to_create:
                    log_job_info("Creating/updating %s TUNNEL relationships in Neo4j...", len(neo4j_edges_to_create))
                    session.execute_write(
                        lambda tx: tx.run(
                            """
                            UNWIND $edges_batch AS edge_data
                            MATCH (src:VPNNode {id: edge_data.source_id})
                            MATCH (dst:VPNNode {id: edge_data.target_id})
                            MERGE (src)-[r:TUNNEL {nautobot_tunnel_pk: edge_data.properties.nautobot_tunnel_pk}]->(dst)
                            SET r = edge_data.properties
                            """,
                            {"edges_batch": neo4j_edges_to_create},
                        )
                    )
                    log_job_debug("Processed %s edges for Neo4j.", len(neo4j_edges_to_create))

                # ---- Update Dashboard Meta (soft-guard counts) ----
                try:
                    dashboard, created = VPNDashboard.objects.get_or_create(
                        id=1,
                        defaults={
                            "last_sync_time": now_utc,
                            "last_sync_status": "Success",
                        },
                    )
                    if not created:
                        dashboard.last_sync_time = now_utc
                        dashboard.last_sync_status = "Success"

                    # Only set counts if these fields exist on the model
                    if hasattr(dashboard, "nodes_count"):
                        dashboard.nodes_count = len(neo4j_nodes_to_create)
                    if hasattr(dashboard, "edges_count"):
                        dashboard.edges_count = len(neo4j_edges_to_create)

                    dashboard.save()
                    log_job_info("Updated VPNDashboard with sync status.")
                except Exception as e:
                    log_job_warning("Failed to update VPNDashboard: %s", e)

                log_job_success(
                    f"Neo4j sync complete. DeviceGroup Nodes: {processed_node_counts['DeviceGroup']}, "
                    f"ManualPeer Nodes: {processed_node_counts['ManualPeer']}, "
                    f"Tunnel Relationships: {edges_synced_count}."
                )

        except Exception as e:
            msg = f"An error occurred during Neo4j sync operations: {e}"
            log_job_failure(msg)
            logger.error("Neo4j Sync Operation Exception Details:", exc_info=True)

            try:
                dashboard, created = VPNDashboard.objects.get_or_create(
                    id=1,
                    defaults={
                        "last_sync_time": now_utc,
                        "last_sync_status": (f"Error: {str(e)[:100]}..." if len(str(e)) > 100 else f"Error: {str(e)}"),
                    },
                )
                if not created:
                    dashboard.last_sync_time = now_utc
                    dashboard.last_sync_status = (
                        f"Error: {str(e)[:100]}..." if len(str(e)) > 100 else f"Error: {str(e)}"
                    )
                    dashboard.save()
            except Exception as dash_err:
                log_job_warning("Failed to update VPNDashboard with error status: %s", dash_err)

            raise RuntimeError(msg) from e
        finally:
            if driver:
                driver.close()
                log_job_info("Neo4j connection closed.")

        return (
            f"Neo4j sync finished. DeviceGroup Nodes: {processed_node_counts['DeviceGroup']}, "
            f"ManualPeer Nodes: {processed_node_counts['ManualPeer']}, "
            f"Tunnels: {edges_synced_count}."
        )


jobs = [SyncNeo4jJob]
