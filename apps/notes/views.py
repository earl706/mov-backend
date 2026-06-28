from apps.common.viewsets import OwnedModelViewSet

from .models import Note
from .serializers import NoteSerializer

class NoteViewSet(OwnedModelViewSet):
    serializer_class = NoteSerializer
    queryset = Note.objects.all().select_related("project")
    filterset_fields = ["project", "task", "is_pinned"]
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "updated_at", "title"]
