from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import OwnedModelViewSet

from .models import Project
from .serializers import ProjectSerializer
from .services import compute_project_health

class ProjectViewSet(OwnedModelViewSet):


    serializer_class = ProjectSerializer
    queryset = Project.objects.all().prefetch_related("tasks")
    filterset_fields = ["status", "is_favorite"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "due_date", "name"]

    def get_queryset(self):
        return super().get_queryset().annotate(num_tasks=Count("tasks"))

    @extend_schema(responses={200: dict})
    @action(detail=True, methods=["get"])
    def health(self, request, pk=None):

        project = self.get_object()
        return Response(compute_project_health(project))
