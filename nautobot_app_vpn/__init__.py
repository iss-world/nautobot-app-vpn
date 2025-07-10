"""App declaration for nautobot_app_vpn."""

from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotAppVpnConfig(NautobotAppConfig):
    """App configuration for the nautobot_app_vpn app."""

    name = "nautobot_app_vpn"
    verbose_name = "VPN"
    version = __version__
    author = "ISS World Services @Powered by NOC"
    description = "Virtual Private Network"
    base_url = "nautobot_app_vpn"
    required_settings = []
    min_version = "2.4.0"
    max_version = "2.9999"
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_app_vpn:docs"
    jobs = "nautobot_app_vpn.jobs"

    def ready(self):
        # Lazy imports to avoid AppRegistryNotReady errors
        super().ready()
        from nautobot.apps import jobs  # pylint: disable=import-outside-toplevel
        from .jobs.sync_neo4j_job import SyncNeo4jJob  # pylint: disable=import-outside-toplevel

        jobs.register_jobs(
            SyncNeo4jJob,
        )


# Required for Nautobot to detect the plugin
config = NautobotAppVpnConfig  # pylint: disable=invalid-name
