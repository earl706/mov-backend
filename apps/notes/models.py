from django.db import models

from apps.common.models import OwnedModel
from apps.projects.models import Project
from apps.tasks.models import Task

class Note(OwnedModel):
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes"
    )


    task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes"
    )
    title = models.CharField(max_length=300)
    content = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_pinned = models.BooleanField(default=False)

    class Meta(OwnedModel.Meta):
        indexes = [models.Index(fields=["owner", "is_pinned"])]

    def __str__(self):
        return self.title
