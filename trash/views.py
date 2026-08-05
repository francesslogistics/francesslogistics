from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TrashedItem
from .serializers import TrashedItemSerializer


class TrashedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read, restore, or permanently delete soft-deleted records.
    Each account only ever sees items IT deleted — see get_queryset().
    Records older than settings.TRASH_RETENTION_DAYS are swept out
    automatically on every list call (mirrors the front-end's
    30-day client-side purge behaviour).
    """
    serializer_class = TrashedItemSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "trash_id"

    def get_queryset(self):
        return TrashedItem.objects.filter(deleted_by=self.request.user)

    def list(self, request, *args, **kwargs):
        self._purge_expired()
        return super().list(request, *args, **kwargs)

    def _purge_expired(self):
        for item in TrashedItem.objects.filter(deleted_by=self.request.user):
            if item.is_expired:
                item.delete()

    @action(detail=True, methods=["post"])
    def restore(self, request, trash_id=None):
        item = self.get_object()
        restored = self._restore_record(item)
        item.delete()
        return Response(
            {"restored": True, "item_type": item.item_type, "record": restored},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def restore_batch(self, request):
        trash_ids = request.data.get("trash_ids", [])
        restored_count = 0
        for item in self.get_queryset().filter(trash_id__in=trash_ids):
            self._restore_record(item)
            item.delete()
            restored_count += 1
        return Response({"restored_count": restored_count})

    @action(detail=False, methods=["post"])
    def delete_batch(self, request):
        trash_ids = request.data.get("trash_ids", [])
        deleted_count, _ = self.get_queryset().filter(trash_id__in=trash_ids).delete()
        return Response({"deleted_count": deleted_count})

    def destroy(self, request, *args, **kwargs):
        # permanent delete, bypassing restore
        return super().destroy(request, *args, **kwargs)

    @staticmethod
    def _restore_record(item: TrashedItem):
        # Imported lazily to avoid app-loading circular imports.
        if item.item_type == TrashedItem.ItemType.BILLING:
            from billing.serializers import BillingRecordSerializer
            data = {k: v for k, v in item.data.items() if k not in ("id", "amount", "status", "created_at", "updated_at", "shipment")}
            serializer = BillingRecordSerializer(data=data)
        elif item.item_type == TrashedItem.ItemType.AGENT:
            from crm.serializers import AgentSerializer
            data = {k: v for k, v in item.data.items() if k not in ("created_at", "updated_at")}
            serializer = AgentSerializer(data=data)
        else:
            return None
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return serializer.data
