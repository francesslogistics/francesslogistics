from django.contrib import admin
from .models import AppSettings


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "email_provider", "sender_email", "updated_at")

    def has_add_permission(self, request):
        # singleton — block creating extra rows from admin
        return not AppSettings.objects.exists()
