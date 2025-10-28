"""UI views for IPSec Crypto Profile management in the VPN plugin."""

import logging

from django.contrib import messages  # Keep for bulk_destroy messages
from django.shortcuts import redirect  # Keep for bulk_destroy redirect
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.api.serializers import IPSecCryptoSerializer
from nautobot_app_vpn.filters import IPSecCryptoFilterSet
from nautobot_app_vpn.forms.ipseccrypto import IPSecCryptoFilterForm, IPSecCryptoForm
from nautobot_app_vpn.models import IPSecCrypto
from nautobot_app_vpn.tables import IPSecCryptoTable

logger = logging.getLogger(__name__)


class IPSecCryptoUIViewSet(NautobotUIViewSet):
    """UI ViewSet for managing IPSec Crypto Profile objects."""

    # Keep standard viewset attributes
    queryset = IPSecCrypto.objects.all()
    serializer_class = IPSecCryptoSerializer
    table_class = IPSecCryptoTable
    form_class = IPSecCryptoForm
    filterset_class = IPSecCryptoFilterSet
    filterset_form_class = IPSecCryptoFilterForm
    default_return_url = "plugins:nautobot_app_vpn:ipseccrypto_list"

    def bulk_destroy(self, request, *args, **kwargs):
        """Bulk delete selected IPSec Crypto Profiles."""
        logger.debug("request.POST: %s", request.POST)
        pks = request.POST.getlist("pk")
        if pks:
            try:
                queryset = self.queryset.filter(pk__in=pks)
                count = queryset.count()
                if count > 0:
                    logger.info(
                        "Deleting %s IPSecCrypto objects: %s",
                        count,
                        list(queryset.values_list("pk", flat=True)),
                    )
                    queryset.delete()
                    messages.success(request, f"Deleted {count} IPSec Crypto profiles.")
                else:
                    messages.warning(request, "No matching profiles found for deletion.")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Error during bulk deletion of IPSecCrypto: %s", exc)
                messages.error(request, "Error deleting profiles: An unexpected error occurred.")
        else:
            messages.warning(request, "No profiles selected for deletion.")
        return redirect(self.get_return_url(request))
