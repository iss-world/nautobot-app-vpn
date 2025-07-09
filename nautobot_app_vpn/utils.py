"""Utility functions for the Nautobot VPN plugin."""

from nautobot.extras.models import Status


def get_default_status():
    """Returns the default Status object for new entries (case-insensitive match on name='Active')."""
    try:
        return Status.objects.get(name__iexact="Active")
    except Status.DoesNotExist:
        return None


def get_valid_statuses():
    """Returns a queryset of valid status options for use in forms or validation."""
    return Status.objects.filter(name__in=["Active", "Planned", "Staging", "Decommissioned", "Down"])
