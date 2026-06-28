from rest_framework.parsers import FormParser, MultiPartParser

from apps.common.viewsets import OwnedModelViewSet

from .models import Attachment
from .serializers import AttachmentSerializer


class AttachmentViewSet(OwnedModelViewSet):
    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["project", "task", "note"]
    ordering_fields = ["created_at", "size", "name"]
