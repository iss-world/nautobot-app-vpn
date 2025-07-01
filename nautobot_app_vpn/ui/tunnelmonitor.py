# nautobot_app_vpn/ui/tunnelmonitor.py
import logging

from django.contrib import messages
from django.shortcuts import redirect
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.api.serializers import TunnelMonitorProfileSerializer  # Ensure this exists
from nautobot_app_vpn.filters import TunnelMonitorProfileFilterSet  # Ensure this exists
from nautobot_app_vpn.forms import TunnelMonitorProfileFilterForm, TunnelMonitorProfileForm

# Import corresponding model, form, filterset, table, serializer
from nautobot_app_vpn.models import TunnelMonitorProfile
from nautobot_app_vpn.tables import TunnelMonitorProfileTable

logger = logging.getLogger(__name__)


class TunnelMonitorProfileUIViewSet(NautobotUIViewSet):
    """UIViewSet for managing Tunnel Monitor Profiles."""

    # Use the model, serializer, table, form, filterset, and filterform defined previously
    queryset = TunnelMonitorProfile.objects.all()
    serializer_class = TunnelMonitorProfileSerializer
    table_class = TunnelMonitorProfileTable
    form_class = TunnelMonitorProfileForm
    filterset_class = TunnelMonitorProfileFilterSet
    filterset_form_class = TunnelMonitorProfileFilterForm

    # Define the default return URL (update in urls.py accordingly)
    default_return_url = "plugins:nautobot_app_vpn:tunnelmonitorprofile_list"
    lookup_field = "pk"  # Standard lookup

    # No custom create/update needed for this simple model initially.
    # Add bulk delete for consistency if desired:
    def bulk_destroy(self, request):
        """Bulk delete selected Tunnel Monitor Profiles."""
        logger.debug(f"request.POST: {request.POST}")
        pks = request.POST.getlist("pk")
        model = self.queryset.model  # Get the model class

        if pks:
            try:
                queryset = model.objects.filter(pk__in=pks)
                # Add protection logic if needed (e.g., check if profile is used by tunnels)
                if queryset.filter(ipsec_tunnels__isnull=False).exists():
                    messages.error(request, "Cannot delete profiles currently in use by IPSec Tunnels.")
                    return redirect(self.get_return_url(request))

                count = queryset.count()
                if count > 0:
                    logger.info(
                        f"Deleting {count} {model._meta.verbose_name_plural}: {list(queryset.values_list('pk', flat=True))}"
                    )
                    queryset.delete()
                    messages.success(request, f"Deleted {count} {model._meta.verbose_name_plural}.")
                else:
                    messages.warning(request, "No matching profiles found for deletion.")
            except Exception as e:
                logger.error(f"Error during bulk deletion of {model._meta.verbose_name_plural}: {e}")
                messages.error(request, "Error deleting profiles: An unexpected error occurred.")
        else:
            messages.warning(request, "No profiles selected for deletion.")
        return redirect(self.get_return_url(request))
