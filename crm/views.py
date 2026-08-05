from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Agent
from .serializers import AgentSerializer
from trash.models import TrashedItem
from trash.utils import move_to_trash


class AgentFilter(filters.FilterSet):
    industry = filters.CharFilter(field_name="industry")

    class Meta:
        model = Agent
        fields = ["industry"]


class AgentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for CRM agents/clients, with nested contacts.
    DELETE moves the record to Trash instead of hard-deleting it.
    """
    queryset = Agent.objects.prefetch_related("contacts").all()
    serializer_class = AgentSerializer
    filterset_class = AgentFilter
    search_fields = ["name", "note", "contacts__name", "contacts__phone", "contacts__email"]
    ordering_fields = ["name", "last_contact", "created_at"]
    lookup_field = "slug"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        move_to_trash(
            instance,
            item_type=TrashedItem.ItemType.AGENT,
            name=instance.name,
            serializer_class=AgentSerializer,
            deleted_by=request.user if request.user.is_authenticated else None,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def industries(self, request):
        values = list(Agent.objects.values_list("industry", flat=True).distinct())
        return Response(values)
