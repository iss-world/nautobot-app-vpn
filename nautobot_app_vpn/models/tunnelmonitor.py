# nautobot_app_vpn/models/tunnelmonitor.py
from django.db import models
from django.urls import reverse  # Ensure reverse is imported
from nautobot.core.models.generics import PrimaryModel
from nautobot.extras.utils import extras_features
from django.core.validators import MinValueValidator


class TunnelMonitorActionChoices(models.TextChoices):
    WAIT_RECOVER = "wait-recover", "Wait Recover"
    FAIL_OVER = "fail-over", "Fail Over"


@extras_features(
    "custom_fields",
    "custom_links",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class TunnelMonitorProfile(PrimaryModel):
    name = models.CharField(max_length=100, unique=True, help_text="Unique name for the Tunnel Monitor Profile.")
    action = models.CharField(
        max_length=20,
        choices=TunnelMonitorActionChoices.choices,
        default=TunnelMonitorActionChoices.WAIT_RECOVER,
        help_text="Action to take when tunnel monitoring detects a failure.",
    )
    interval = models.PositiveIntegerField(
        default=3, validators=[MinValueValidator(1)], help_text="Probe interval in seconds."
    )
    threshold = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Number of consecutive failed probes before triggering action.",
    )

    class Meta:
        verbose_name = "Tunnel Monitor Profile"
        verbose_name_plural = "Tunnel Monitor Profiles"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # --- CORRECTED URL Name ---
        # Use the name shown in show_urls (without _detail)
        return reverse("plugins:nautobot_app_vpn:tunnelmonitorprofile", kwargs={"pk": self.pk})
        # --- END CORRECTION ---
