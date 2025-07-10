"""UI views for IKE Gateway management in the VPN plugin."""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.api.serializers import IKEGatewaySerializer
from nautobot_app_vpn.filters import IKEGatewayFilterSet
from nautobot_app_vpn.forms.ikegateway import IKEGatewayFilterForm, IKEGatewayForm
from nautobot_app_vpn.models import IKEGateway
from nautobot_app_vpn.tables import IKEGatewayTable

logger = logging.getLogger(__name__)


class IKEGatewayUIViewSet(NautobotUIViewSet):
    """UI ViewSet for managing IKE Gateway objects."""

    queryset = IKEGateway.objects.select_related("ike_crypto_profile", "bind_interface", "status").prefetch_related(
        "local_devices", "peer_devices", "local_locations", "peer_locations"
    )

    # Core NautobotUIViewSet attributes
    serializer_class = IKEGatewaySerializer
    table_class = IKEGatewayTable
    form_class = IKEGatewayForm
    filterset_class = IKEGatewayFilterSet
    filterset_form_class = IKEGatewayFilterForm
    default_return_url = "plugins:nautobot_app_vpn:ikegateway_list"

    def bulk_destroy(self, request, *args, **kwargs):
        """Bulk delete selected IKE Gateways."""

        logger.debug("request.POST: %s", request.POST)
        pks = request.POST.getlist("pk")
        if pks:
            try:
                queryset = self.queryset.model.objects.filter(pk__in=pks)
                count = queryset.count()
                if count > 0:
                    logger.info(
                        "Deleting %s IKEGateway objects: %s",
                        count,
                        list(queryset.values_list("pk", flat=True)),
                    )
                    queryset.delete()
                    messages.success(request, f"Deleted {count} IKE Gateways.")
                else:
                    messages.warning(request, "No matching gateways found for deletion.")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Error during bulk deletion of IKEGateway: %s", exc)
                messages.error(request, "Error deleting gateways: An unexpected error occurred.")
        else:
            messages.warning(request, "No gateways selected for deletion.")
        return redirect(self.get_return_url(request))
