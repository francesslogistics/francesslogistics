from django.db import models


class AppSettings(models.Model):
    """
    Singleton row holding the dashboard's global preferences
    (mirrors the front-end's in-memory `appSettings` object, but persisted).
    """
    notify_new_shipments = models.BooleanField(default=True)
    notify_task_updates = models.BooleanField(default=True)
    notify_overdue = models.BooleanField(default=True)
    email_provider = models.CharField(max_length=30, default="gmail")
    sender_email = models.EmailField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App settings"
        verbose_name_plural = "App settings"

    def __str__(self):
        return "Application Settings"

    def save(self, *args, **kwargs):
        # enforce a single row (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Inquiry(models.Model):
    """A submission from the public 'Request a Quote' page (quote.html).
    Field names below track the numbered questions on that form (1-13,
    plus 10.5 for the conditional dangerous-goods documents) so it's easy
    to see the mapping. Shows up under the Inquiries nav so staff can
    triage it or reach out via 'Contact Client'."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CONVERTED = "converted", "Converted"
        CLOSED = "closed", "Closed"

    # 1-5: Contact info
    full_name = models.CharField(max_length=150, blank=True, default="")
    company = models.CharField(max_length=150, blank=True, default="")
    phone = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    # 6-8: Shipment details
    shipment_type = models.CharField(max_length=30, blank=True, default="")  # Import / Export / Other
    shipment_type_other = models.CharField(max_length=100, blank=True, default="")
    mode = models.CharField(max_length=10, blank=True, default="")  # Air / Sea / Land
    origin = models.CharField(max_length=150, blank=True, default="")
    destination = models.CharField(max_length=150, blank=True, default="")
    # 9-12: Cargo details
    cargo = models.TextField(blank=True, default="")  # description of goods/dimension
    dangerous_goods = models.CharField(max_length=5, blank=True, default="")  # Yes / No
    quantity_type = models.CharField(max_length=20, blank=True, default="")  # Pallets / Boxes
    quantity_count = models.CharField(max_length=30, blank=True, default="")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"Inquiry({self.full_name})"


def inquiry_upload_path(instance, filename):
    return f"inquiries/{instance.inquiry_id}/{instance.kind}/{filename}"


class InquiryFile(models.Model):
    """One uploaded file for an inquiry — either a 10.5 dangerous-goods
    document or a 13 proof-of-goods attachment."""

    class Kind(models.TextChoices):
        DG_DOC = "dg", "Dangerous goods document (10.5)"
        PROOF = "proof", "Proof of goods (13)"

    inquiry = models.ForeignKey(Inquiry, related_name="files", on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    file = models.FileField(upload_to=inquiry_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"InquiryFile({self.inquiry_id}, {self.kind}, {self.file.name})"
