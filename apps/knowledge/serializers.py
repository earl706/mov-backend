from rest_framework import serializers

from .models import Link, Person


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "uuid", "name", "role", "email", "avatar_url", "created_at"]
        read_only_fields = ["id", "uuid", "created_at"]


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = [
            "id",
            "uuid",
            "source_type",
            "source_id",
            "target_type",
            "target_id",
            "relation",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "created_at"]
