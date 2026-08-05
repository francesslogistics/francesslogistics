from rest_framework import serializers
from .models import AppSettings, Inquiry, InquiryFile


class AppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSettings
        fields = [
            "notify_new_shipments",
            "notify_task_updates",
            "notify_overdue",
            "email_provider",
            "sender_email",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class InquiryFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InquiryFile
        fields = ["id", "kind", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class InquirySerializer(serializers.ModelSerializer):
    files = InquiryFileSerializer(many=True, read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id", "full_name", "company", "phone", "email", "address",
            "shipment_type", "shipment_type_other", "mode", "origin", "destination",
            "cargo", "dangerous_goods", "quantity_type", "quantity_count",
            "status", "files", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
