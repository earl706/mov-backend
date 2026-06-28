from rest_framework import serializers

from .models import CalendarEvent


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = [
            "id",
            "uuid",
            "title",
            "description",
            "kind",
            "start",
            "end",
            "all_day",
            "color",
            "project",
            "task",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "created_at"]

    def validate(self, attrs):
        start = attrs.get("start", getattr(self.instance, "start", None))
        end = attrs.get("end", getattr(self.instance, "end", None))
        if start and end and end < start:
            raise serializers.ValidationError("Event end must be after its start.")
        return attrs
