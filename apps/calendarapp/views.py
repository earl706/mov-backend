from apps.common.viewsets import OwnedModelViewSet

from .models import CalendarEvent
from .serializers import CalendarEventSerializer

class CalendarEventViewSet(OwnedModelViewSet):


    serializer_class = CalendarEventSerializer
    queryset = CalendarEvent.objects.all()
    filterset_fields = {
        "kind": ["exact"],
        "project": ["exact"],
        "start": ["gte", "lte"],
    }
    search_fields = ["title", "description"]
    ordering_fields = ["start", "end"]
