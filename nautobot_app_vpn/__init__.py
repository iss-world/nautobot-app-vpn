"""App declaration for nautobot_app_vpn. 1.0.4"""
# pylint: disable=import-outside-toplevel

from importlib import metadata
from django.conf import settings
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
    min_version = "3.0.0"
    max_version = "3.0.99"
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_app_vpn:docs"
    jobs = "nautobot_app_vpn.jobs"

    def ready(self):
        # Existing startup logic
        super().ready()

        spectacular_settings = getattr(settings, "SPECTACULAR_SETTINGS", None)
        if spectacular_settings is None:
            spectacular_settings = {}
            settings.SPECTACULAR_SETTINGS = spectacular_settings

        if not spectacular_settings.get("DISABLE_ERRORS_AND_WARNINGS"):
            spectacular_settings["DISABLE_ERRORS_AND_WARNINGS"] = True

        enum_overrides = spectacular_settings.setdefault("ENUM_NAME_OVERRIDES", {})
        enum_overrides.setdefault(
            "IdentificationTypeEnum",
            "nautobot_app_vpn.models.constants.IdentificationTypes",
        )
        enum_overrides.setdefault(
            "IPAddressTypeEnum",
            "nautobot_app_vpn.models.constants.IPAddressTypes",
        )

        from nautobot.apps import jobs  # pylint: disable=import-outside-toplevel
        from .jobs.sync_neo4j_job import SyncNeo4jJob  # pylint: disable=import-outside-toplevel

        jobs.register_jobs(
            SyncNeo4jJob,
        )


config = NautobotAppVpnConfig  # pylint: disable=invalid-name
