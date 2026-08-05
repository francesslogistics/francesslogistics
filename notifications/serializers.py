from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "icon", "color", "text", "read",
            "target_view", "target_bill_type", "target_bill_status", "target_row_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
