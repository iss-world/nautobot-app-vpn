# nautobot_app_vpn/ui/ikecrypto.py
import logging

from django.contrib import messages  # Keep for bulk_destroy messages
from django.shortcuts import redirect  # Keep for bulk_destroy redirect
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.api.serializers import IKECryptoSerializer
from nautobot_app_vpn.filters import IKECryptoFilterSet
from nautobot_app_vpn.forms.ikecrypto import IKECryptoFilterForm, IKECryptoForm
from nautobot_app_vpn.models import IKECrypto
from nautobot_app_vpn.tables import IKECryptoProfileTable

logger = logging.getLogger(__name__)


class IKECryptoUIViewSet(NautobotUIViewSet):
    model = IKECrypto
    # Keep standard viewset attributes
    queryset = IKECrypto.objects.all()
    filterset_class = IKECryptoFilterSet
    filterset_form_class = IKECryptoFilterForm
    form_class = IKECryptoForm
    table_class = IKECryptoProfileTable
    serializer_class = IKECryptoSerializer  # Required for schema generation
    default_return_url = "plugins:nautobot_app_vpn:ikecrypto_list"

    # This powers the "Delete" button on the list view when items are selected
    def bulk_destroy(self, request):
        """Bulk delete selected profiles."""
        logger.debug(f"request.POST: {request.POST}")
        pks = request.POST.getlist("pk")
        if pks:
            try:
                # You might want to add protection logic here, e.g., check if profile is in use
                queryset = self.queryset.filter(pk__in=pks)
                count = queryset.count()
                if count > 0:
                    logger.info(f"Deleting {count} IKECrypto objects: {list(queryset.values_list('pk', flat=True))}")
                    queryset.delete()
                    messages.success(request, f"Deleted {count} IKE Crypto profiles.")
                else:
                    messages.warning(request, "No matching profiles found for deletion.")

            except Exception as e:
                logger.error(f"Error during bulk deletion of IKECrypto: {e}")
                messages.error(request, f"Error deleting profiles: {e}")
        else:
            messages.warning(request, "No profiles selected for deletion.")
        # Use get_return_url() which respects the ?return_url= query param
        return redirect(self.get_return_url(request))
