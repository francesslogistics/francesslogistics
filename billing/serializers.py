from rest_framework import serializers
from .models import BillingRecord, Quotation


class BillingRecordSerializer(serializers.ModelSerializer):
    shipment = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    created_by_photo = serializers.SerializerMethodField()

    class Meta:
        model = BillingRecord
        fields = [
            "id", "category", "vendor", "client",
            "shipment_origin", "shipment_dest", "shipment_scope", "shipment", "awb",
            "invoice_date", "credit_line", "due_date",
            "currency", "status", "source",
            "si_number", "si_amount", "si_entries", "less_2307", "soa_number", "soa_amount", "soa_entries",
            "amount", "created_by_name", "created_by_photo",
            "job_ref", "sold_tin", "sold_address", "mbl", "carrier", "vessel_flight",
            "no_kgs_vol", "er", "etd_eta", "zero_rated", "discount",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "amount", "due_date", "status", "created_at", "updated_at", "created_by_name", "created_by_photo"]

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return ""
        profile = getattr(obj.created_by, "profile", None)
        return profile.display_name if profile else obj.created_by.username

    def get_created_by_photo(self, obj):
        profile = getattr(obj.created_by, "profile", None) if obj.created_by else None
        return profile.photo if profile else ""

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        vendor = attrs.get("vendor", getattr(self.instance, "vendor", ""))
        client = attrs.get("client", getattr(self.instance, "client", ""))
        if category == BillingRecord.Category.PAYABLE and not vendor:
            raise serializers.ValidationError({"vendor": "Vendor is required for payables."})
        if category == BillingRecord.Category.RECEIVABLE and not client:
            raise serializers.ValidationError({"client": "Client is required for receivables."})
        return attrs


class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = [
            "id", "invoice_no", "sold_name", "sold_tin", "sold_address",
            "job_ref", "so_no", "issued_date", "credit_terms",
            "origin", "destination", "carrier", "vessel_flight", "no_kgs_vol",
            "hbl", "mbl", "etd_eta", "er",
            "vatable_items", "non_vatable_items",
            "vatable_sales", "zero_rated_sales", "vat_exempt_sales", "less_discount", "less_withholding",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
