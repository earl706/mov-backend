from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.tasks.models import Task

from .models import Project
from .services import compute_project_health

User = get_user_model()


class ProjectHealthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("p@x.com", "pass12345")

    def test_empty_project_neutral_health(self):
        project = Project.objects.create(owner=self.user, name="Empty")
        health = compute_project_health(project)
        self.assertEqual(health["progress"], 0.0)
        self.assertEqual(health["total_tasks"], 0)

    def test_progress_reflects_completion(self):
        project = Project.objects.create(owner=self.user, name="P")
        Task.objects.create(owner=self.user, project=project, status="done",
                            completed_at=timezone.now())
        Task.objects.create(owner=self.user, project=project, status="todo")
        health = compute_project_health(project)
        self.assertEqual(health["progress"], 50.0)
        self.assertEqual(health["open_tasks"], 1)


class ProjectAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("p2@x.com", "pass12345")
        self.client.force_authenticate(self.user)

    def test_create_includes_health(self):
        resp = self.client.post("/api/projects/", {"name": "New"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertIn("health", resp.data)

    def test_health_action(self):
        project = Project.objects.create(owner=self.user, name="P")
        resp = self.client.get(f"/api/projects/{project.id}/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("confidence", resp.data)
