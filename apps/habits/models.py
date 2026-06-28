from django.db import models

from apps.common.models import OwnedModel


class Habit(OwnedModel):
    CADENCE = [("daily", "Daily"), ("weekly", "Weekly")]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cadence = models.CharField(max_length=10, choices=CADENCE, default="daily")
    target_per_period = models.PositiveSmallIntegerField(default=1)
    color = models.CharField(max_length=9, default="#10b981")
    icon = models.CharField(max_length=40, default="sparkles")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class HabitLog(models.Model):
    """A single completion entry. Uniqueness per (habit, date) keeps idempotency
    for daily check-ins while still allowing weekly habits multiple logs."""

    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["habit", "date"])]

    def __str__(self):
        return f"{self.habit.name} @ {self.date}"
