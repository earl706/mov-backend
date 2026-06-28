from rest_framework import serializers

from .models import FocusSession, WorkContextSnapshot


class FocusSessionSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = FocusSession
        fields = [
            "id",
            "uuid",
            "task",
            "task_title",
            "label",
            "started_at",
            "ended_at",
            "planned_minutes",
            "actual_minutes",
            "interruptions",
            "quality",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "created_at"]


class WorkContextSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkContextSnapshot
        fields = ["id", "uuid", "label", "items", "active_task", "created_at"]
        read_only_fields = ["id", "uuid", "created_at"]
