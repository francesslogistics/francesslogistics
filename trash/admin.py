from django.contrib import admin
from .models import TrashedItem


@admin.register(TrashedItem)
class TrashedItemAdmin(admin.ModelAdmin):
    list_display = ("name", "item_type", "deleted_by", "deleted_at", "purge_at", "is_expired")
    list_filter = ("item_type", "deleted_by")
    search_fields = ("name", "original_id")
