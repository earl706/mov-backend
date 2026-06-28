from rest_framework import serializers

from .models import Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "uuid",
            "file",
            "url",
            "name",
            "content_type",
            "size",
            "project",
            "task",
            "note",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "url", "size", "created_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        url = obj.file.url
        return request.build_absolute_uri(url) if request and url.startswith("/") else url

    def create(self, validated_data):
        upload = validated_data.get("file")
        if upload is not None:
            validated_data.setdefault("content_type", getattr(upload, "content_type", ""))
        return super().create(validated_data)
