from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import OwnedModelViewSet

from .models import Habit, HabitLog
from .serializers import HabitLogSerializer, HabitSerializer

class HabitViewSet(OwnedModelViewSet):


    serializer_class = HabitSerializer
    queryset = Habit.objects.all().prefetch_related("logs")
    filterset_fields = ["cadence", "is_active"]
    search_fields = ["name", "description"]

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, pk=None):

        habit = self.get_object()
        today = timezone.localdate()
        log, created = HabitLog.objects.get_or_create(
            habit=habit, date=today, defaults={"note": request.data.get("note", "")}
        )
        return Response(
            HabitSerializer(habit, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="undo")
    def undo(self, request, pk=None):

        habit = self.get_object()
        HabitLog.objects.filter(habit=habit, date=timezone.localdate()).delete()
        return Response(HabitSerializer(habit, context=self.get_serializer_context()).data)

class HabitLogViewSet(viewsets.ModelViewSet):
    serializer_class = HabitLogSerializer
    filterset_fields = ["habit", "date"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return HabitLog.objects.none()
        return HabitLog.objects.filter(habit__owner=self.request.user)
