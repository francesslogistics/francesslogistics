import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


class TrashedItem(models.Model):
    """
    Generic soft-delete bin. Any deletable record in the system (billing
    record, CRM agent, ...) gets snapshotted here instead of being hard
    deleted. Records auto-purge after TRASH_RETENTION_DAYS (default 30).
    """

    class ItemType(models.TextChoices):
        BILLING = "billing", "Billing record"
        AGENT = "agent", "CRM agent / client"

    trash_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    name = models.CharField(max_length=200, help_text="Display name shown in the Trash list")
    original_id = models.CharField(max_length=64, help_text="Primary key of the record before deletion")
    data = models.JSONField(help_text="Full snapshot of the record, used to restore it")
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="trashed_items", help_text="Who deleted this record — each account only sees its own trash.",
    )

    deleted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-deleted_at"]

    def __str__(self):
        return f"[{self.item_type}] {self.name} (deleted {self.deleted_at:%Y-%m-%d})"

    @property
    def purge_at(self):
        days = getattr(settings, "TRASH_RETENTION_DAYS", 30)
        return self.deleted_at + timedelta(days=days)

    @property
    def is_expired(self):
        return timezone.now() >= self.purge_at
