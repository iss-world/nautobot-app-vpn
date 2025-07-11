"""UI views for IPsec Tunnel management in the VPN plugin."""

import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from nautobot.apps.views import NautobotUIViewSet

from nautobot_app_vpn.api.serializers import IPSECTunnelSerializer
from nautobot_app_vpn.filters import IPSECTunnelFilterSet
from nautobot_app_vpn.forms import IPSecProxyIDFormSet, IPSECTunnelFilterForm, IPSECTunnelForm

# Import models, forms, etc.
from nautobot_app_vpn.models import IPSECTunnel
from nautobot_app_vpn.tables import IPSECTunnelTable

logger = logging.getLogger(__name__)


class IPSECTunnelUIViewSet(NautobotUIViewSet):
    """UI ViewSet for managing IPsec Tunnel objects."""

    queryset = IPSECTunnel.objects.select_related(
        "ike_gateway",
        "ipsec_crypto_profile",
        "status",
        "tunnel_interface",
        "monitor_profile",
    ).prefetch_related(
        "devices",
        "proxy_ids",
    )

    serializer_class = IPSECTunnelSerializer
    table_class = IPSECTunnelTable
    form_class = IPSECTunnelForm
    filterset_class = IPSECTunnelFilterSet
    filterset_form_class = IPSECTunnelFilterForm
    default_return_url = "plugins:nautobot_app_vpn:ipsectunnel_list"

    def create(self, request, *args, **kwargs):
        """Handle creation of IPSec Tunnel and its associated Proxy IDs."""

        object_type = self.form_class._meta.model._meta.verbose_name
        template_name = f"{self.form_class._meta.model._meta.app_label}/ipsectunnel_edit.html"

        form = self.form_class(request.POST or None)
        formset = IPSecProxyIDFormSet(request.POST or None, prefix="proxy_ids")

        if request.method == "POST":
            if form.is_valid():
                try:
                    instance = form.save()
                    formset.instance = instance

                    if formset.is_valid():
                        formset.save()
                        messages.success(request, f"✅ {object_type} created successfully.")
                        if "_add_another" in request.POST:
                            return redirect(request.path)
                        return redirect(self.get_return_url(request, instance))

                    logger.error("❌ ProxyID Formset validation errors: %s", formset.errors)
                    try:
                        instance.delete()
                        logger.info("Deleted partially created tunnel %s due to formset error.", instance.pk)
                    except Exception as del_err:  # pylint: disable=broad-exception-caught
                        logger.error("Error deleting partially created tunnel %s: %s", instance.pk, del_err)
                    messages.error(request, "❌ Failed to create proxy IDs. Please check the Proxy ID section.")

                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.error("❌ Error saving %s: %s", object_type, e, exc_info=True)
                    messages.error(request, f"❌ Failed to create {object_type}: {e}")
            else:
                logger.error("❌ Main Tunnel Form validation errors: %s", form.errors.as_json())
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
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.error("❌ Error updating %s '%s': %s", object_type, instance, e, exc_info=True)
                    messages.error(request, f"❌ Failed to update {object_type}: {e}")
            else:
                if not form.is_valid():
                    logger.error("❌ Main Tunnel Form validation errors: %s", form.errors.as_json())
                    messages.error(request, "❌ Failed to update tunnel. Please check the main form.")
                if not formset.is_valid():
                    logger.error("❌ ProxyID Formset validation errors: %s", formset.errors)
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

    def bulk_destroy(self, request, *args, **kwargs):
        """Handle bulk deletion of IPsec Tunnel objects."""

        logger.debug("request.POST: %s", request.POST)
        pks = request.POST.getlist("pk")
        model = self.queryset.model
        if pks:
            try:
                queryset = model.objects.filter(pk__in=pks)
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
                    messages.warning(request, "No matching tunnels found for deletion.")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Error during bulk deletion of %s: %s", model._meta.verbose_name_plural, exc)
                messages.error(request, "Error deleting tunnels: An unexpected error occurred.")
        else:
            messages.warning(request, "No tunnels selected for deletion.")
        return redirect(self.get_return_url(request))
