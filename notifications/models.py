from django.db import models


class Notification(models.Model):
    """Mirrors the front-end's `notifications` array/bell panel."""

    icon = models.CharField(max_length=40, default="bell", help_text="lucide-icon name")
    color = models.CharField(max_length=30, default="var(--gold)", help_text="CSS color/var used by the bell icon")
    text = models.CharField(max_length=255)
    read = models.BooleanField(default=False)

    # where clicking the notification should navigate to
    target_view = models.CharField(max_length=40, blank=True, default="")
    target_bill_type = models.CharField(max_length=20, blank=True, default="")
    target_bill_status = models.CharField(max_length=20, blank=True, default="")
    target_row_id = models.CharField(max_length=80, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text
