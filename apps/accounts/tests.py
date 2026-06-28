from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AuthFlowTests(APITestCase):
    def test_register_creates_user_and_profile(self):
        resp = self.client.post(
            "/api/auth/register/",
            {"email": "new@x.com", "password": "supersecret1", "full_name": "New"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(email="new@x.com")
        # Profile auto-created by signal.
        self.assertTrue(hasattr(user, "profile"))

    def test_login_returns_tokens_and_user(self):
        User.objects.create_user("login@x.com", "supersecret1")
        resp = self.client.post(
            "/api/auth/login/", {"email": "login@x.com", "password": "supersecret1"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("user", resp.data)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_profile_update(self):
        user = User.objects.create_user("prof@x.com", "supersecret1")
        self.client.force_authenticate(user)
        resp = self.client.patch(
            "/api/auth/profile/", {"weight_importance": 2.5, "chronotype": "early"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.weight_importance, 2.5)
        self.assertEqual(user.profile.chronotype, "early")
