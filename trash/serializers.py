from rest_framework import serializers
from .models import TrashedItem


class TrashedItemSerializer(serializers.ModelSerializer):
    purge_at = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    deleted_by_username = serializers.CharField(source="deleted_by.username", read_only=True, default="")

    class Meta:
        model = TrashedItem
        fields = [
            "id", "trash_id", "item_type", "name", "original_id",
            "data", "deleted_at", "purge_at", "is_expired",
            "deleted_by", "deleted_by_username",
        ]
        read_only_fields = fields
