from django.conf import settings
from django.db import models


class Profile(models.Model):
    """
    Extra, non-auth info about a user — the stuff the front-end's sidebar
    profile block shows (position, avatar) that django.contrib.auth's User
    model doesn't have a field for. Username/password live on User itself;
    this table is deliberately small and only holds display info.
    """

    class Position(models.TextChoices):
        CEO = "CEO", "CEO"
        SALES_ACCOUNT_MANAGER = "Sales Account Manager", "Sales Account Manager"
        SALES_ACCOUNT_EXECUTIVE = "Sales Account Executive", "Sales Account Executive"
        INTERN = "Intern", "Intern"

    # Fixed rank order (highest first). A user can only change the position of
    # someone who ranks strictly below them, and can never assign a position
    # at or above their own rank — this is enforced in accounts/views.py, not
    # just the front-end, so it can't be bypassed via direct API calls.
    RANK = {
        Position.CEO: 4,
        Position.SALES_ACCOUNT_MANAGER: 3,
        Position.SALES_ACCOUNT_EXECUTIVE: 2,
        Position.INTERN: 1,
    }

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    # Restricted to a fixed list of job titles — rendered as a dropdown
    # (Django admin / DRF ChoiceField) rather than free text.
    position = models.CharField(max_length=40, choices=Position.choices, blank=True, default="")
    # Stored as a data: URL (base64) for now, same as the front-end's local-only
    # mode — swap for a real ImageField + media storage once file uploads are set up.
    photo = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.username})"

    @property
    def rank(self):
        return self.RANK.get(self.position, 0)

    @property
    def display_name(self):
        full = self.user.get_full_name()
        return full or self.user.username
