from django.db import models

from apps.common.models import OwnedModel
from apps.tasks.models import Task

class FocusSession(OwnedModel):


    task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="focus_sessions"
    )
    label = models.CharField(max_length=200, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    planned_minutes = models.PositiveIntegerField(default=25)
    actual_minutes = models.PositiveIntegerField(default=0)
    planned_seconds = models.PositiveIntegerField(default=0)
    actual_seconds = models.PositiveIntegerField(default=0)
    interruptions = models.PositiveSmallIntegerField(default=0)
    quality = models.PositiveSmallIntegerField(default=3)
    notes = models.TextField(blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["owner", "started_at"])]

    def __str__(self):
        return self.label or f"Focus {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def duration_seconds(self):
        return self.actual_seconds or self.actual_minutes * 60

    @property
    def planned_duration_seconds(self):
        return self.planned_seconds or self.planned_minutes * 60

class WorkContextSnapshot(OwnedModel):


    label = models.CharField(max_length=200, blank=True)
    items = models.JSONField(default=list)
    active_task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    def __str__(self):
        return self.label or f"Snapshot {self.created_at:%Y-%m-%d %H:%M}"
