from django.db import models
from django.utils.text import slugify


class Agent(models.Model):
    """
    A CRM record for a local or international freight agent/client.
    Mirrors the front-end's `crmClients` array.
    """

    class Industry(models.TextChoices):
        LOCAL = "Local Agent", "Local Agent"
        INTERNATIONAL = "International Agent", "International Agent"

    slug = models.SlugField(max_length=220, unique=True, blank=True)
    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=30, choices=Industry.choices, default=Industry.LOCAL)
    note = models.CharField(max_length=255, blank=True, default="No transactions yet")
    last_contact = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "agent"
            slug = base
            n = 1
            while Agent.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)


class Contact(models.Model):
    """A contact person belonging to an Agent."""
    agent = models.ForeignKey(Agent, related_name="contacts", on_delete=models.CASCADE)
    name = models.CharField(max_length=150, blank=True, default="")
    phone = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "id"]

    def __str__(self):
        return self.name or "Unnamed contact"
