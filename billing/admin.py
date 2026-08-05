from django.contrib import admin
from .models import BillingRecord, Quotation


@admin.register(BillingRecord)
class BillingRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "vendor", "client", "amount", "currency", "status", "due_date")
    list_filter = ("category", "status", "currency")
    search_fields = ("vendor", "client", "awb", "si_number", "soa_number")


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice_no", "sold_name", "job_ref", "created_at")
    search_fields = ("invoice_no", "sold_name", "job_ref")
