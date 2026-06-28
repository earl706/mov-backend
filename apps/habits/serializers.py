from rest_framework import serializers

from .models import Habit, HabitLog
from .momentum import compute_momentum

class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = ["id", "habit", "date", "note", "created_at"]
        read_only_fields = ["id", "created_at"]

class HabitSerializer(serializers.ModelSerializer):
    momentum = serializers.SerializerMethodField()
    recent_logs = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = [
            "id",
            "uuid",
            "name",
            "description",
            "cadence",
            "target_per_period",
            "color",
            "icon",
            "is_active",
            "momentum",
            "recent_logs",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "created_at"]

    def get_momentum(self, obj):
        dates = [log.date for log in obj.logs.all()]
        return compute_momentum(dates, obj.cadence, obj.target_per_period)

    def get_recent_logs(self, obj):
        return [log.date for log in obj.logs.all()[:60]]
