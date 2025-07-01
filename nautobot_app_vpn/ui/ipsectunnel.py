# nautobot_app_vpn/ui/ipsectunnel.py
import logging
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from nautobot.apps.views import NautobotUIViewSet

# Import models, forms, etc.
from nautobot_app_vpn.models import IPSECTunnel, IKEGateway, IPSecCrypto, IPSecProxyID, TunnelMonitorProfile
from nautobot_app_vpn.forms import IPSECTunnelForm, IPSecProxyIDFormSet, IPSECTunnelFilterForm
from nautobot_app_vpn.filters import IPSECTunnelFilterSet
from nautobot_app_vpn.api.serializers import IPSECTunnelSerializer
from nautobot_app_vpn.tables import IPSECTunnelTable

logger = logging.getLogger(__name__)


class IPSECTunnelUIViewSet(NautobotUIViewSet):
    """UIViewSet for IPSec Tunnels with support for formsets."""

    # --- CORRECTED queryset definition ---
    queryset = IPSECTunnel.objects.select_related(
        # ForeignKeys go here:
        "ike_gateway",
        "ipsec_crypto_profile",
        "status",
        "tunnel_interface",
        "monitor_profile",
    ).prefetch_related(
        "devices",  # M2M field (Changed from device)
        "proxy_ids",  # M2M field (reverse relationship)
    )
    # --- End CORRECTED queryset ---

    serializer_class = IPSECTunnelSerializer
    table_class = IPSECTunnelTable
    form_class = IPSECTunnelForm
    filterset_class = IPSECTunnelFilterSet
    filterset_form_class = IPSECTunnelFilterForm
    default_return_url = "plugins:nautobot_app_vpn:ipsectunnel_list"

    # Keep custom create/update methods for formset handling
    # ... (create and update methods remain as previously defined) ...
    def create(self, request, *args, **kwargs):
        """Handle creation of IPSec Tunnel and its associated Proxy IDs."""
        object_type = self.form_class._meta.model._meta.verbose_name
        template_name = f"{self.form_class._meta.model._meta.app_label}/ipsectunnel_edit.html"  # Adjust if needed

        form = self.form_class(request.POST or None)
        formset = IPSecProxyIDFormSet(request.POST or None, prefix="proxy_ids")

        if request.method == "POST":
            if form.is_valid():
                try:
                    instance = form.save()  # Should handle M2M 'devices' correctly
                    formset.instance = instance

                    if formset.is_valid():
                        formset.save()
                        messages.success(request, f"✅ {object_type} created successfully.")
                        if "_add_another" in request.POST:
                            return redirect(request.path)
                        return redirect(self.get_return_url(request, instance))
                    else:
                        logger.error(f"❌ ProxyID Formset validation errors: {formset.errors}")
                        try:
                            instance.delete()
                            logger.info(f"Deleted partially created tunnel {instance.pk} due to formset error.")
                        except Exception as del_err:
                            logger.error(f"Error deleting partially created tunnel {instance.pk}: {del_err}")
                        messages.error(request, "❌ Failed to create proxy IDs. Please check the Proxy ID section.")
                except Exception as e:
                    logger.error(f"❌ Error saving {object_type}: {e}", exc_info=True)
                    messages.error(request, f"❌ Failed to create {object_type}: {e}")
            else:
                logger.error(f"❌ Main Tunnel Form validation errors: {form.errors.as_json()}")
                messages.error(request, f"❌ Failed to create {object_type}. Please check the main form.")

        return render(
            request,
            template_name,
            {
                "object": None,
                "object_type": object_type,
                "form": form,
                "formset": formset,
                "return_url": self.get_return_url(request),
                "editing": False,
            },
        )

    def update(self, request, *args, **kwargs):
        """Handle updates to IPSec Tunnel and its associated Proxy IDs."""
        instance = get_object_or_404(self.queryset, pk=kwargs["pk"])
        object_type = self.form_class._meta.model._meta.verbose_name
        template_name = f"{self.form_class._meta.model._meta.app_label}/ipsectunnel_edit.html"

        form = self.form_class(request.POST or None, instance=instance)
        formset = IPSecProxyIDFormSet(request.POST or None, instance=instance, prefix="proxy_ids")

        if request.method == "POST":
            if form.is_valid() and formset.is_valid():
                try:
                    instance = form.save()
                    formset.save()
                    messages.success(request, f"✅ Modified {object_type} '{instance}'.")
                    return redirect(self.get_return_url(request, instance))
                except Exception as e:
                    logger.error(f"❌ Error updating {object_type} '{instance}': {e}", exc_info=True)
                    messages.error(request, f"❌ Failed to update {object_type}: {e}")
            else:
                if not form.is_valid():
                    logger.error(f"❌ Main Tunnel Form validation errors: {form.errors.as_json()}")
                    messages.error(request, "❌ Failed to update tunnel. Please check the main form.")
                if not formset.is_valid():
                    logger.error(f"❌ ProxyID Formset validation errors: {formset.errors}")
                    messages.error(request, "❌ Failed to update proxy IDs. Please check the Proxy ID section.")

        return render(
            request,
            template_name,
            {
                "object": instance,
                "object_type": object_type,
                "form": form,
                "formset": formset,
                "return_url": self.get_return_url(request, instance),
                "editing": True,
            },
        )

    # Keep bulk_destroy if needed
    def bulk_destroy(self, request):
        # ... (Keep existing bulk_destroy logic) ...
        logger.debug(f"request.POST: {request.POST}")
        pks = request.POST.getlist("pk")
        model = self.queryset.model
        if pks:
            try:
                queryset = model.objects.filter(pk__in=pks)
                count = queryset.count()
                if count > 0:
                    logger.info(
                        f"Deleting {count} {model._meta.verbose_name_plural}: {list(queryset.values_list('pk', flat=True))}"
                    )
                    queryset.delete()
                    messages.success(request, f"Deleted {count} {model._meta.verbose_name_plural}.")
                else:
                    messages.warning(request, "No matching tunnels found for deletion.")
            except Exception as e:
                logger.error(f"Error during bulk deletion of {model._meta.verbose_name_plural}: {e}")
                messages.error(request, f"Error deleting tunnels: An unexpected error occurred.")
        else:
            messages.warning(request, "No tunnels selected for deletion.")
        return redirect(self.get_return_url(request))
