from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BillingRecord, Quotation
from .serializers import BillingRecordSerializer, QuotationSerializer
from trash.models import TrashedItem
from trash.utils import move_to_trash


class BillingRecordFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category")
    status = filters.CharFilter(field_name="status")
    currency = filters.CharFilter(field_name="currency")

    class Meta:
        model = BillingRecord
        fields = ["category", "status", "currency"]


class BillingRecordViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for payables & receivables.
    DELETE moves the record to Trash instead of hard-deleting it,
    matching the dashboard's recoverable-delete behaviour.
    """
    queryset = BillingRecord.objects.all()
    serializer_class = BillingRecordSerializer
    filterset_class = BillingRecordFilter
    search_fields = ["vendor", "client", "shipment_origin", "shipment_dest", "awb", "si_number", "soa_number"]
    ordering_fields = ["invoice_date", "due_date", "amount", "created_at"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        display_name = instance.vendor if instance.category == BillingRecord.Category.PAYABLE else instance.client
        move_to_trash(
            instance,
            item_type=TrashedItem.ItemType.BILLING,
            name=display_name or "Untitled invoice",
            serializer_class=BillingRecordSerializer,
            deleted_by=request.user if request.user.is_authenticated else None,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="batch-delete")
    def batch_delete(self, request):
        ids = request.data.get("ids", [])
        moved = 0
        for instance in BillingRecord.objects.filter(id__in=ids):
            display_name = instance.vendor if instance.category == BillingRecord.Category.PAYABLE else instance.client
            move_to_trash(
                instance,
                item_type=TrashedItem.ItemType.BILLING,
                name=display_name or "Untitled invoice",
                serializer_class=BillingRecordSerializer,
                deleted_by=request.user if request.user.is_authenticated else None,
            )
            moved += 1
        return Response({"moved_to_trash": moved})

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        instance = self.get_object()
        instance.status = BillingRecord.Status.PAID
        instance.save()
        return Response(self.get_serializer(instance).data)


class QuotationViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for standalone saved SI/SOA sheets (the Quotation page's
    "Saved billing invoices" list) — separate from BillingRecord, which
    covers ledger-derived payables/receivables instead.
    """
    queryset = Quotation.objects.all()
    serializer_class = QuotationSerializer

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)
