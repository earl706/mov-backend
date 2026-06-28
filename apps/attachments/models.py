import os

from django.db import models

from apps.common.models import OwnedModel
from apps.notes.models import Note
from apps.projects.models import Project
from apps.tasks.models import Task


def upload_to(instance, filename):
    # Partition by owner to keep buckets tidy and avoid collisions.
    return f"attachments/{instance.owner_id}/{filename}"


class Attachment(OwnedModel):
    """A user-uploaded file stored via django-storages.

    The same model works against local disk, AWS S3 or DigitalOcean Spaces — the
    storage backend is selected globally by STORAGE_BACKEND, so this code never
    needs to know where the bytes live. Attachments may optionally be linked to a
    project, task or note.
    """

    file = models.FileField(upload_to=upload_to)
    name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveBigIntegerField(default=0)

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name="attachments"
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True, blank=True, related_name="attachments"
    )
    note = models.ForeignKey(
        Note, on_delete=models.CASCADE, null=True, blank=True, related_name="attachments"
    )

    def save(self, *args, **kwargs):
        if self.file and not self.name:
            self.name = os.path.basename(self.file.name)
        if self.file and not self.size:
            try:
                self.size = self.file.size
            except (OSError, ValueError):
                self.size = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.file.name
