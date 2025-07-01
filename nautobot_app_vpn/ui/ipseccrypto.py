# nautobot_app_vpn/ui/ipseccrypto.py
import logging
from django.contrib import messages  # Keep for bulk_destroy messages
from django.shortcuts import redirect  # Keep for bulk_destroy redirect

from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.models import IPSecCrypto
from nautobot_app_vpn.forms.ipseccrypto import IPSecCryptoForm, IPSecCryptoFilterForm
from nautobot_app_vpn.filters import IPSecCryptoFilterSet
from nautobot_app_vpn.tables import IPSecCryptoProfileTable
from nautobot_app_vpn.api.serializers import IPSecCryptoSerializer

logger = logging.getLogger(__name__)


class IPSecCryptoUIViewSet(NautobotUIViewSet):
    """UIViewSet for IPSec Crypto Profiles."""  # Removed mention of clone/import

    # Keep standard viewset attributes
    queryset = IPSecCrypto.objects.all()
    serializer_class = IPSecCryptoSerializer  # Required for schema generation
    table_class = IPSecCryptoProfileTable
    form_class = IPSecCryptoForm
    filterset_class = IPSecCryptoFilterSet
    filterset_form_class = IPSecCryptoFilterForm
    default_return_url = "plugins:nautobot_app_vpn:ipseccrypto_list"

    # --- Keep Bulk Delete Method (Optional - Remove if not needed) ---
    def bulk_destroy(self, request):
        """Bulk delete selected IPSec Crypto Profiles."""
        logger.debug(f"request.POST: {request.POST}")
        pks = request.POST.getlist("pk")
        if pks:
            try:
                # Add protection logic if needed (e.g., check if profile is used by gateways/tunnels)
                queryset = self.queryset.filter(pk__in=pks)
                count = queryset.count()
                if count > 0:
                    logger.info(f"Deleting {count} IPSecCrypto objects: {list(queryset.values_list('pk', flat=True))}")
                    # Add checks here to prevent deletion if related objects exist, if desired
                    # e.g., if queryset.filter(Q(crypto_tunnels__isnull=False)).exists():
                    #          messages.error(request, "Cannot delete profiles that are currently in use by IPSec Tunnels.")
                    #          return redirect(self.get_return_url(request))
                    queryset.delete()
                    messages.success(request, f"Deleted {count} IPSec Crypto profiles.")
                else:
                    messages.warning(request, "No matching profiles found for deletion.")
            except Exception as e:
                logger.error(f"Error during bulk deletion of IPSecCrypto: {e}")
                # Be careful about exposing raw exception details
                messages.error(request, f"Error deleting profiles: An unexpected error occurred.")
        else:
            messages.warning(request, "No profiles selected for deletion.")
        return redirect(self.get_return_url(request))
