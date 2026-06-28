from django.db import models

from apps.common.models import OwnedModel

class Project(OwnedModel):
    STATUS = [
        ("active", "Active"),
        ("on_hold", "On hold"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=9, default="#6366f1")
    status = models.CharField(max_length=16, choices=STATUS, default="active")
    due_date = models.DateField(null=True, blank=True)
    is_favorite = models.BooleanField(default=False)

    class Meta(OwnedModel.Meta):
        indexes = [models.Index(fields=["owner", "status"])]

    def __str__(self):
        return self.name
