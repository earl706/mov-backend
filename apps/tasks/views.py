from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import OwnedModelViewSet
from rest_framework import viewsets

from .decomposition import decompose
from .models import Subtask, Task
from .scoring import score_task
from .serializers import SubtaskSerializer, TaskSerializer, TaskWriteSerializer

def user_completion_rate(user, days=30):

    since = timezone.now() - timedelta(days=days)
    qs = Task.objects.filter(owner=user, created_at__gte=since)
    total = qs.count()
    if not total:
        return 0.5
    done = qs.filter(status="done").count()
    return round(done / total, 3)

class TaskViewSet(OwnedModelViewSet):


    queryset = Task.objects.all().prefetch_related("subtasks").select_related("project")
    filterset_fields = ["status", "project", "importance", "urgency"]
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "created_at", "order", "importance", "urgency"]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return TaskWriteSerializer
        return TaskSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.user.is_authenticated:
            ctx["completion_rate"] = user_completion_rate(self.request.user)
        return ctx

    @action(detail=False, methods=["get"])
    def prioritized(self, request):

        weights = request.user.profile.weights()
        rate = user_completion_rate(request.user)
        tasks = list(
            self.get_queryset().exclude(status="done").prefetch_related("subtasks")
        )
        scored = sorted(
            tasks,
            key=lambda t: score_task(t, weights=weights, completion_rate=rate)["score"],
            reverse=True,
        )
        serializer = self.get_serializer(scored, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.mark_status("done")
        return Response(TaskSerializer(task, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="set-status")
    def set_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get("status")
        valid = dict(Task.STATUS)
        if new_status not in valid:
            return Response(
                {"status": f"Must be one of {list(valid)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        task.mark_status(new_status)
        return Response(TaskSerializer(task, context=self.get_serializer_context()).data)

    @extend_schema(request=None, responses={201: SubtaskSerializer(many=True)})
    @action(detail=True, methods=["post"])
    def decompose(self, request, pk=None):

        task = self.get_object()
        task.subtasks.filter(ai_generated=True).delete()
        proposals = decompose(task.title, task.description)
        created = [
            Subtask.objects.create(task=task, **proposal) for proposal in proposals
        ]
        return Response(
            SubtaskSerializer(created, many=True).data, status=status.HTTP_201_CREATED
        )

class SubtaskViewSet(viewsets.ModelViewSet):


    serializer_class = SubtaskSerializer
    filterset_fields = ["task", "is_done"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Subtask.objects.none()
        return Subtask.objects.filter(task__owner=self.request.user).select_related("task")

    def perform_create(self, serializer):

        task = serializer.validated_data["task"]
        if task.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Cannot add subtasks to another user's task.")
        serializer.save()
