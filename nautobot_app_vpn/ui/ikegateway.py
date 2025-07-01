# nautobot_app_vpn/ui/ikegateway.py
import logging
from django.contrib import messages
from django.shortcuts import redirect  # Keep redirect for bulk_destroy

from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.models import IKEGateway
from nautobot_app_vpn.forms.ikegateway import IKEGatewayForm, IKEGatewayFilterForm
from nautobot_app_vpn.filters import IKEGatewayFilterSet
from nautobot_app_vpn.tables import IKEGatewayTable
from nautobot_app_vpn.api.serializers import IKEGatewaySerializer

logger = logging.getLogger(__name__)


class IKEGatewayUIViewSet(NautobotUIViewSet):
    """UIViewSet for IKE Gateways."""

    # Queryset with optimizations
    queryset = IKEGateway.objects.select_related("ike_crypto_profile", "bind_interface", "status").prefetch_related(
        "local_devices", "peer_devices", "local_locations", "peer_locations"
    )

    # Core NautobotUIViewSet attributes
    serializer_class = IKEGatewaySerializer
    table_class = IKEGatewayTable
    form_class = IKEGatewayForm  # Use the fixed form with workaround
    filterset_class = IKEGatewayFilterSet
    filterset_form_class = IKEGatewayFilterForm
    default_return_url = "plugins:nautobot_app_vpn:ikegateway_list"

    # No custom create/update methods needed now, relying on default behavior

    # Keep bulk_destroy if needed
    def bulk_destroy(self, request):
        """Bulk delete selected IKE Gateways."""
        logger.debug(f"request.POST: {request.POST}")
        pks = request.POST.getlist("pk")
        if pks:
            try:
                queryset = self.queryset.model.objects.filter(pk__in=pks)
                count = queryset.count()
                if count > 0:
                    # Optional: Add checks before deletion
                    # if queryset.filter(tunnels__isnull=False).exists():
                    #    messages.error(request, "Cannot delete gateways currently used by IPSec Tunnels.")
                    #    return redirect(self.get_return_url(request))
                    logger.info(f"Deleting {count} IKEGateway objects: {list(queryset.values_list('pk', flat=True))}")
                    queryset.delete()
                    messages.success(request, f"Deleted {count} IKE Gateways.")
                else:
                    messages.warning(request, "No matching gateways found for deletion.")
            except Exception as e:
                logger.error(f"Error during bulk deletion of IKEGateway: {e}")
                messages.error(request, f"Error deleting gateways: An unexpected error occurred.")
        else:
            messages.warning(request, "No gateways selected for deletion.")
        return redirect(self.get_return_url(request))
