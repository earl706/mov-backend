from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Subtask, Task
from .scoring import score_task

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = [
            "id",
            "task",
            "title",
            "is_done",
            "estimated_minutes",
            "order",
            "ai_generated",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "ai_generated"]

class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, read_only=True)
    subtask_progress = serializers.FloatField(read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    priority = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "uuid",
            "project",
            "project_name",
            "title",
            "description",
            "status",
            "importance",
            "urgency",
            "estimated_minutes",
            "due_date",
            "started_at",
            "completed_at",
            "tags",
            "order",
            "subtasks",
            "subtask_progress",
            "priority",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "started_at", "completed_at", "created_at", "updated_at"]

    @extend_schema_field(serializers.DictField())
    def get_priority(self, obj):

        request = self.context.get("request")
        weights = None
        if request and request.user.is_authenticated and hasattr(request.user, "profile"):
            weights = request.user.profile.weights()
        completion_rate = self.context.get("completion_rate", 0.5)
        return score_task(obj, weights=weights, completion_rate=completion_rate)

class TaskWriteSerializer(TaskSerializer):


    class Meta(TaskSerializer.Meta):
        pass
