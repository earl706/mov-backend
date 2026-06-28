from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import OwnedModelViewSet
from apps.notes.models import Note
from apps.tasks.models import Task

from .models import FocusSession, WorkContextSnapshot
from .serializers import FocusSessionSerializer, WorkContextSnapshotSerializer

class FocusSessionViewSet(OwnedModelViewSet):
    serializer_class = FocusSessionSerializer
    queryset = FocusSession.objects.all().select_related("task")
    filterset_fields = ["task", "quality"]
    ordering_fields = ["started_at", "actual_minutes"]

    @action(detail=False, methods=["get"])
    def today(self, request):

        start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sessions = self.get_queryset().filter(started_at__gte=start)
        total_seconds = sum(s.actual_seconds or s.actual_minutes * 60 for s in sessions)
        goal = getattr(request.user.profile, "daily_focus_goal_minutes", 120)
        goal_seconds = goal * 60
        return Response(
            {
                "minutes": round(total_seconds / 60, 1),
                "seconds": total_seconds,
                "goal_minutes": goal,
                "goal_seconds": goal_seconds,
                "sessions": sessions.count(),
                "progress": round(100 * total_seconds / goal_seconds, 1) if goal_seconds else 0,
            }
        )

class WorkContextSnapshotViewSet(OwnedModelViewSet):


    serializer_class = WorkContextSnapshotSerializer
    queryset = WorkContextSnapshot.objects.all()

    @action(detail=False, methods=["get"])
    def recover(self, request):
        since = timezone.now() - timedelta(hours=48)
        recent_tasks = (
            Task.objects.filter(owner=request.user, updated_at__gte=since)
            .exclude(status="done")
            .order_by("-updated_at")[:5]
        )
        recent_notes = Note.objects.filter(
            owner=request.user, updated_at__gte=since
        ).order_by("-updated_at")[:5]

        items = [
            {"type": "task", "id": t.id, "uuid": str(t.uuid), "title": t.title}
            for t in recent_tasks
        ] + [
            {"type": "note", "id": n.id, "uuid": str(n.uuid), "title": n.title}
            for n in recent_notes
        ]
        return Response({"items": items, "generated_at": timezone.now()})
