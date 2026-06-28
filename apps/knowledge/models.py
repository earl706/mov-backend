from django.db import models

from apps.common.models import OwnedModel

class Person(OwnedModel):


    name = models.CharField(max_length=200)
    role = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Link(OwnedModel):


    ENTITY_TYPES = [
        ("project", "Project"),
        ("task", "Task"),
        ("note", "Note"),
        ("habit", "Habit"),
        ("file", "File"),
        ("person", "Person"),
    ]

    source_type = models.CharField(max_length=16, choices=ENTITY_TYPES)
    source_id = models.PositiveIntegerField()
    target_type = models.CharField(max_length=16, choices=ENTITY_TYPES)
    target_id = models.PositiveIntegerField()
    relation = models.CharField(max_length=60, default="related_to")

    class Meta(OwnedModel.Meta):
        unique_together = [
            ("owner", "source_type", "source_id", "target_type", "target_id", "relation")
        ]

    def __str__(self):
        return f"{self.source_type}:{self.source_id} -{self.relation}-> {self.target_type}:{self.target_id}"
