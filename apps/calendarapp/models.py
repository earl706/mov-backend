from django.db import models

from apps.common.models import OwnedModel
from apps.projects.models import Project
from apps.tasks.models import Task

class CalendarEvent(OwnedModel):
    KIND = [
        ("event", "Event"),
        ("focus_block", "Focus block"),
        ("deadline", "Deadline"),
        ("meeting", "Meeting"),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=16, choices=KIND, default="event")
    start = models.DateTimeField()
    end = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    color = models.CharField(max_length=9, default="#6366f1")

    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
    )
    task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
    )

    class Meta(OwnedModel.Meta):
        ordering = ["start"]
        indexes = [models.Index(fields=["owner", "start"])]

    def __str__(self):
        return f"{self.title} ({self.start:%Y-%m-%d %H:%M})"
