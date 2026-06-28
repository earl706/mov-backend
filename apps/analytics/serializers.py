from rest_framework import serializers

from .models import Retrospective

class RetrospectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retrospective
        fields = [
            "id",
            "uuid",
            "week_start",
            "headline",
            "summary",
            "highlights",
            "suggestions",
            "metrics",
            "created_at",
        ]
        read_only_fields = fields
