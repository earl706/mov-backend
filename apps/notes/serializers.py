from rest_framework import serializers

from .models import Note

class NoteSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "uuid",
            "project",
            "project_name",
            "task",
            "title",
            "content",
            "tags",
            "is_pinned",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]
