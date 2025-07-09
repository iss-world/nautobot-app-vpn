"""UI views for IKE Crypto Profiles in the VPN plugin."""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.api.serializers import IKECryptoSerializer
from nautobot_app_vpn.filters import IKECryptoFilterSet
from nautobot_app_vpn.forms.ikecrypto import IKECryptoFilterForm, IKECryptoForm
from nautobot_app_vpn.models import IKECrypto
from nautobot_app_vpn.tables import IKECryptoProfileTable

logger = logging.getLogger(__name__)


class IKECryptoUIViewSet(NautobotUIViewSet):
    """UI ViewSet for IKE Crypto profiles."""

    model = IKECrypto
    queryset = IKECrypto.objects.all()
    filterset_class = IKECryptoFilterSet
    filterset_form_class = IKECryptoFilterForm
    form_class = IKECryptoForm
    table_class = IKECryptoProfileTable
    serializer_class = IKECryptoSerializer
    default_return_url = "plugins:nautobot_app_vpn:ikecrypto_list"

    def bulk_destroy(self, request):
        """Handle bulk deletion of IKECrypto objects with logging and feedback."""

        logger.debug(f"request.POST: {request.POST}")
        pks = request.POST.getlist("pk")
        if pks:
            try:
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

        return redirect(self.get_return_url(request))
