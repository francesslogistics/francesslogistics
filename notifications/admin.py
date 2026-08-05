from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("text", "read", "target_view", "created_at")
    list_filter = ("read", "target_view")
