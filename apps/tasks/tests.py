from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from .decomposition import decompose
from .models import Subtask, Task
from .scoring import score_task

User = get_user_model()


class ScoringTests(APITestCase):
    """Unit tests for the pure prioritization function."""

    def _make(self, **kw):
        defaults = dict(importance=3, urgency=3, estimated_minutes=30)
        defaults.update(kw)
        return Task(**defaults)

    def test_score_is_bounded_0_100(self):
        task = self._make(importance=5, urgency=5, due_date=timezone.now())
        result = score_task(task)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertIn("factors", result)

    def test_overdue_scores_higher_than_far_future(self):
        overdue = self._make(due_date=timezone.now() - timedelta(days=1))
        future = self._make(due_date=timezone.now() + timedelta(days=20))
        self.assertGreater(score_task(overdue)["score"], score_task(future)["score"])

    def test_weights_change_ranking(self):
        important = self._make(importance=5, urgency=1)
        urgent = self._make(importance=1, urgency=5)
        # Heavily weight importance: the important task should win.
        weights = {"importance": 5, "urgency": 0.1, "deadline": 0.1, "effort": 0.1, "completion_history": 0.1}
        self.assertGreater(
            score_task(important, weights=weights)["score"],
            score_task(urgent, weights=weights)["score"],
        )


class DecompositionTests(APITestCase):
    def test_recognizes_writing_archetype(self):
        subs = decompose("Write a blog post about momentum")
        self.assertTrue(any("draft" in s["title"].lower() for s in subs))
        self.assertTrue(all(s["ai_generated"] for s in subs))

    def test_generic_fallback(self):
        subs = decompose("Xyzzy frobnicate")
        self.assertGreaterEqual(len(subs), 1)


class TaskAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("a@x.com", "pass12345")
        self.other = User.objects.create_user("b@x.com", "pass12345")
        self.client.force_authenticate(self.user)

    def test_create_and_list_task(self):
        resp = self.client.post("/api/tasks/", {"title": "Test task"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertIn("priority", resp.data)
        resp = self.client.get("/api/tasks/")
        self.assertEqual(resp.data["count"], 1)

    def test_owner_isolation(self):
        Task.objects.create(owner=self.other, title="hidden")
        resp = self.client.get("/api/tasks/")
        self.assertEqual(resp.data["count"], 0)

    def test_decompose_creates_subtasks(self):
        task = Task.objects.create(owner=self.user, title="Build a new feature")
        resp = self.client.post(f"/api/tasks/{task.id}/decompose/")
        self.assertEqual(resp.status_code, 201)
        self.assertGreater(Subtask.objects.filter(task=task, ai_generated=True).count(), 0)
        # Re-running should not duplicate AI subtasks.
        before = Subtask.objects.filter(task=task).count()
        self.client.post(f"/api/tasks/{task.id}/decompose/")
        self.assertEqual(Subtask.objects.filter(task=task).count(), before)

    def test_complete_sets_timestamp(self):
        task = Task.objects.create(owner=self.user, title="finish me")
        resp = self.client.post(f"/api/tasks/{task.id}/complete/")
        self.assertEqual(resp.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "done")
        self.assertIsNotNone(task.completed_at)

    def test_prioritized_endpoint_returns_sorted(self):
        Task.objects.create(owner=self.user, title="low", importance=1, urgency=1)
        Task.objects.create(owner=self.user, title="high", importance=5, urgency=5,
                            due_date=timezone.now())
        resp = self.client.get("/api/tasks/prioritized/")
        self.assertEqual(resp.status_code, 200)
        scores = [t["priority"]["score"] for t in resp.data]
        self.assertEqual(scores, sorted(scores, reverse=True))
