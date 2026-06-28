"""User accounts and the adaptive productivity profile.

The `ProductivityProfile` is the heart of Mov's personalization: it stores the
weights that drive task prioritization and a rolling snapshot of behavioural
metrics that the analytics layer recomputes. Recommendations elsewhere read from
this profile so that personalization is centralized and explainable.
"""
import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Email-as-username manager."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    # Drop username; authenticate by email.
    username = None
    email = models.EmailField(unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class ProductivityProfile(models.Model):
    """Per-user personalization state.

    Scoring weights are normalized client- and server-side but stored raw so a
    user can express, e.g., "deadlines matter twice as much as effort to me".
    `chronotype` and `focus_window_*` let predictive scheduling place work where
    the user is historically most effective.
    """

    CHRONOTYPES = [
        ("early", "Early bird"),
        ("balanced", "Balanced"),
        ("night", "Night owl"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Task prioritization weights (see apps.tasks.scoring).
    weight_importance = models.FloatField(default=1.0)
    weight_urgency = models.FloatField(default=1.0)
    weight_deadline = models.FloatField(default=1.2)
    weight_effort = models.FloatField(default=0.8)
    weight_completion_history = models.FloatField(default=0.6)

    chronotype = models.CharField(max_length=16, choices=CHRONOTYPES, default="balanced")
    focus_window_start = models.PositiveSmallIntegerField(default=9)  # hour of day
    focus_window_end = models.PositiveSmallIntegerField(default=12)
    daily_focus_goal_minutes = models.PositiveIntegerField(default=120)

    # Rolling behavioural snapshot (recomputed by analytics; cached here for speed).
    momentum_score = models.FloatField(default=50.0)
    burnout_risk = models.FloatField(default=0.0)  # 0..1
    consistency_score = models.FloatField(default=50.0)

    updated_at = models.DateTimeField(auto_now=True)

    def weights(self):
        return {
            "importance": self.weight_importance,
            "urgency": self.weight_urgency,
            "deadline": self.weight_deadline,
            "effort": self.weight_effort,
            "completion_history": self.weight_completion_history,
        }

    def __str__(self):
        return f"Profile<{self.user.email}>"
