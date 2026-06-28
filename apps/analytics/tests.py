from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.focus.models import FocusSession
from apps.tasks.models import Task

from .services import (
    behavioral_intelligence,
    build_retrospective,
    burnout_risk,
    momentum_score,
    predictive_schedule,
)

User = get_user_model()


class BehavioralIntelligenceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("bi@x.com", "pass12345")

    def _focus(self, days_ago, minutes=60, interruptions=0, quality=4, hour=10):
        start = timezone.now().replace(hour=hour, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
        return FocusSession.objects.create(
            owner=self.user, started_at=start, ended_at=start + timedelta(minutes=minutes),
            actual_minutes=minutes, interruptions=interruptions, quality=quality,
        )

    def test_behavioral_payload_shape(self):
        self._focus(1)
        data = behavioral_intelligence(self.user, days=7)
        for key in ("focus_by_day", "context_switching", "consistency", "momentum", "burnout_risk"):
            self.assertIn(key, data)

    def test_burnout_rises_with_overwork_and_late_nights(self):
        for d in range(10):
            self._focus(d, minutes=360, quality=2, hour=23)  # long, low-quality, late
        self.assertGreater(burnout_risk(self.user), 0.4)

    def test_momentum_zero_for_inactive_user(self):
        self.assertEqual(momentum_score(self.user), 0.0)

    def test_predictive_schedule_returns_confidences(self):
        Task.objects.create(
            owner=self.user, title="due soon", due_date=timezone.now() + timedelta(days=2),
            estimated_minutes=60,
        )
        result = predictive_schedule(self.user)
        self.assertEqual(len(result["predictions"]), 1)
        self.assertTrue(0 <= result["predictions"][0]["confidence"] <= 1)


class RetrospectiveTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("retro@x.com", "pass12345")
        self.client.force_authenticate(self.user)

    def test_generate_endpoint(self):
        resp = self.client.post("/api/retrospectives/generate/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("headline", resp.data)
        self.assertIn("suggestions", resp.data)

    def test_build_is_idempotent_per_week(self):
        r1 = build_retrospective(self.user)
        r2 = build_retrospective(self.user)
        self.assertEqual(r1.id, r2.id)

    def test_dashboard_endpoint(self):
        resp = self.client.get("/api/dashboard/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("counts", resp.data)
