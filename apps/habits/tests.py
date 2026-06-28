from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Habit
from .momentum import compute_momentum

User = get_user_model()


class MomentumTests(APITestCase):
    def test_perfect_recent_history_high_momentum(self):
        today = date(2024, 1, 31)
        dates = [today - timedelta(days=i) for i in range(30)]
        result = compute_momentum(dates, today=today)
        self.assertGreater(result["momentum"], 90)
        self.assertEqual(result["current_streak"], 30)

    def test_single_miss_does_not_zero_momentum(self):
        """The key differentiator: a gap should not reset momentum to 0."""
        today = date(2024, 1, 31)
        dates = [today - timedelta(days=i) for i in range(30) if i != 2]
        result = compute_momentum(dates, today=today)
        self.assertGreater(result["momentum"], 80)

    def test_empty_history(self):
        result = compute_momentum([], today=date(2024, 1, 31))
        self.assertEqual(result["momentum"], 0.0)
        self.assertEqual(result["current_streak"], 0)


class HabitAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("h@x.com", "pass12345")
        self.client.force_authenticate(self.user)

    def test_check_in_is_idempotent(self):
        habit = Habit.objects.create(owner=self.user, name="Read")
        r1 = self.client.post(f"/api/habits/{habit.id}/check-in/")
        self.assertEqual(r1.status_code, 201)
        r2 = self.client.post(f"/api/habits/{habit.id}/check-in/")
        self.assertEqual(r2.status_code, 200)  # already logged today
        self.assertEqual(habit.logs.count(), 1)

    def test_undo_removes_today(self):
        habit = Habit.objects.create(owner=self.user, name="Read")
        self.client.post(f"/api/habits/{habit.id}/check-in/")
        self.client.post(f"/api/habits/{habit.id}/undo/")
        self.assertEqual(habit.logs.count(), 0)
