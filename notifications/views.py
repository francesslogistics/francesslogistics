from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        return Response({"unread": Notification.objects.filter(read=False).count()})

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = Notification.objects.filter(read=False).update(read=True)
        return Response({"marked_read": updated})

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.read = True
        notif.save(update_fields=["read"])
        return Response(self.get_serializer(notif).data)

    @action(detail=False, methods=["delete"], url_path="clear-all")
    def clear_all(self, request):
        deleted, _ = Notification.objects.all().delete()
        return Response({"deleted": deleted})
