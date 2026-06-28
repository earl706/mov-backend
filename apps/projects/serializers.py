from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Project
from .services import compute_project_health


class ProjectSerializer(serializers.ModelSerializer):
    health = serializers.SerializerMethodField()
    task_count = serializers.IntegerField(source="tasks.count", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "uuid",
            "name",
            "description",
            "color",
            "status",
            "due_date",
            "is_favorite",
            "task_count",
            "health",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    @extend_schema_field(serializers.DictField())
    def get_health(self, obj):
        # `tasks` is prefetched in the viewset to avoid N+1 queries.
        return compute_project_health(obj, tasks=obj.tasks.all())
