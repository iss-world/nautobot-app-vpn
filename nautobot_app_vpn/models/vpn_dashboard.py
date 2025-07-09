"""Register custom VPN dashboard views for the Nautobot App VPN plugin."""

from django.db import models
from nautobot.core.models import BaseModel


class VPNDashboard(BaseModel):
    """Model to store VPN Dashboard statistics and metadata."""

    name = models.CharField(max_length=100, unique=True, help_text="Dashboard name")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last time dashboard was updated")

    # ✅ VPN Status Metrics
    total_tunnels = models.PositiveIntegerField(default=0, help_text="Total VPN tunnels")
    active_tunnels = models.PositiveIntegerField(default=0, help_text="Number of active VPN tunnels")
    inactive_tunnels = models.PositiveIntegerField(default=0, help_text="Number of inactive VPN tunnels")

    # ✅ Sync and Push Status
    last_sync_status = models.CharField(
        max_length=50,
        # Consider adding "running", "skipped" to choices if needed based on job logic
        choices=[
            ("success", "Success"),
            ("failed", "Failed"),
            ("pending", "Pending"),
            ("running", "Running"),
            ("skipped", "Skipped"),
        ],
        default="pending",
        help_text="Status of the last sync",
    )
    last_sync_time = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp of last sync run started"
    )  # Changed help_text slightly
    last_push_status = models.CharField(
        max_length=50,
        choices=[("success", "Success"), ("failed", "Failed"), ("pending", "Pending")],  # Add running/skipped if needed
        default="pending",
        help_text="Status of last VPN configuration push",
    )
    last_push_time = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last successful config push")

    class Meta:
        verbose_name = "VPN Dashboard"
        verbose_name_plural = "VPN Dashboards"

    def __str__(self):
        return f"{self.name} (Updated: {self.last_updated})"
