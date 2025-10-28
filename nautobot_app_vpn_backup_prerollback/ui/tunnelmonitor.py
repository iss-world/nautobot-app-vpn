"""UI views for Tunnel Monitor Profile management in the VPN plugin."""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.api.serializers import TunnelMonitorProfileSerializer
from nautobot_app_vpn.filters import TunnelMonitorProfileFilterSet
from nautobot_app_vpn.forms import TunnelMonitorProfileFilterForm, TunnelMonitorProfileForm


from nautobot_app_vpn.models import TunnelMonitorProfile
from nautobot_app_vpn.tables import TunnelMonitorProfileTable

logger = logging.getLogger(__name__)


class TunnelMonitorProfileUIViewSet(NautobotUIViewSet):
    """UI ViewSet for managing Tunnel Monitor Profile objects."""

    queryset = TunnelMonitorProfile.objects.all()
    serializer_class = TunnelMonitorProfileSerializer
    table_class = TunnelMonitorProfileTable
    form_class = TunnelMonitorProfileForm
    filterset_class = TunnelMonitorProfileFilterSet
    filterset_form_class = TunnelMonitorProfileFilterForm

    default_return_url = "plugins:nautobot_app_vpn:tunnelmonitorprofile_list"
    lookup_field = "pk"

    def bulk_destroy(self, request, *args, **kwargs):
        """Handle bulk deletion of Tunnel Monitor Profile objects."""

        logger.debug("request.POST: %s", request.POST)
        pks = request.POST.getlist("pk")
        model = self.queryset.model

        if pks:
            try:
                queryset = model.objects.filter(pk__in=pks)

                if queryset.filter(ipsec_tunnels__isnull=False).exists():
                    messages.error(request, "Cannot delete profiles currently in use by IPSec Tunnels.")
                    return redirect(self.get_return_url(request))

                count = queryset.count()
                if count > 0:
                    logger.info(
                        "Deleting %s %s: %s",
                        count,
                        model._meta.verbose_name_plural,
                        list(queryset.values_list("pk", flat=True)),
                    )
                    queryset.delete()
                    messages.success(request, f"Deleted {count} {model._meta.verbose_name_plural}.")
                else:
                    messages.warning(request, "No matching profiles found for deletion.")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Error during bulk deletion of %s: %s", model._meta.verbose_name_plural, exc)
                messages.error(request, "Error deleting profiles: An unexpected error occurred.")
        else:
            messages.warning(request, "No profiles selected for deletion.")
        return redirect(self.get_return_url(request))
