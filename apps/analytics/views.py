from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.habits.models import Habit
from apps.notes.models import Note
from apps.projects.models import Project
from apps.tasks.models import Task

from .models import Retrospective
from .serializers import RetrospectiveSerializer
from .services import (
    behavioral_intelligence,
    build_retrospective,
    discover_patterns,
    predictive_schedule,
    timeline_activity,
    update_profile_snapshot,
)


def _days_param(request, default=30, maximum=365):
    try:
        days = int(request.query_params.get("days", default))
    except (TypeError, ValueError):
        days = default
    return max(1, min(maximum, days))


class DashboardView(APIView):
    """Aggregated counts and quick stats for the home dashboard."""

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        tasks = Task.objects.filter(owner=user)
        due_today = tasks.filter(
            due_date__date=today
        ).exclude(status="done").count()
        overdue = tasks.filter(
            due_date__lt=timezone.now()
        ).exclude(status="done").count()
        completed_week = tasks.filter(
            status="done", completed_at__date__gte=today - timedelta(days=7)
        ).count()
        bi = behavioral_intelligence(user, days=14)
        return Response(
            {
                "counts": {
                    "projects": Project.objects.filter(owner=user).exclude(status="archived").count(),
                    "open_tasks": tasks.exclude(status="done").count(),
                    "due_today": due_today,
                    "overdue": overdue,
                    "completed_this_week": completed_week,
                    "habits": Habit.objects.filter(owner=user, is_active=True).count(),
                    "notes": Note.objects.filter(owner=user).count(),
                },
                "momentum": bi["momentum"],
                "consistency": bi["consistency"],
                "burnout_risk": bi["burnout_risk"],
                "focus_by_day": bi["focus_by_day"][-7:],
            }
        )


class BehavioralIntelligenceView(APIView):
    @extend_schema(parameters=[OpenApiParameter("days", int)], responses={200: dict})
    def get(self, request):
        days = _days_param(request)
        data = behavioral_intelligence(request.user, days=days)
        # Keep the cached profile snapshot fresh on each dashboard view.
        update_profile_snapshot(request.user)
        return Response(data)


class PatternsView(APIView):
    def get(self, request):
        return Response({"patterns": discover_patterns(request.user)})


class PredictiveScheduleView(APIView):
    @extend_schema(parameters=[OpenApiParameter("horizon_days", int)], responses={200: dict})
    def get(self, request):
        try:
            horizon = int(request.query_params.get("horizon_days", 7))
        except (TypeError, ValueError):
            horizon = 7
        return Response(predictive_schedule(request.user, horizon_days=max(1, min(30, horizon))))


class TimelineView(APIView):
    @extend_schema(parameters=[OpenApiParameter("days", int)], responses={200: dict})
    def get(self, request):
        days = _days_param(request, default=180, maximum=365)
        return Response({"days": days, "timeline": timeline_activity(request.user, days=days)})


class RetrospectiveViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Browse weekly retrospectives; `generate` builds the current week on demand."""

    serializer_class = RetrospectiveSerializer
    queryset = Retrospective.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Retrospective.objects.none()
        return Retrospective.objects.filter(owner=self.request.user)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        retro = build_retrospective(request.user)
        return Response(RetrospectiveSerializer(retro).data)
