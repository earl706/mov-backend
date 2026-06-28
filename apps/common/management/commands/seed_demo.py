"""Seed realistic demonstration data for the Mov platform.

Creates a demo user with several months of plausible activity so that every
analytics and intelligence feature has something meaningful to show.

Usage:
    python manage.py seed_demo            # create/refresh demo data
    python manage.py seed_demo --if-empty # no-op if a demo user already exists
    python manage.py seed_demo --flush    # delete demo user first, then reseed
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.services import build_retrospective, update_profile_snapshot
from apps.calendarapp.models import CalendarEvent
from apps.focus.models import FocusSession
from apps.habits.models import Habit, HabitLog
from apps.knowledge.models import Link, Person
from apps.notes.models import Note
from apps.notifications.models import Notification
from apps.projects.models import Project
from apps.tasks.decomposition import decompose
from apps.tasks.models import Subtask, Task

User = get_user_model()

DEMO_EMAIL = "demo@mov.app"
DEMO_PASSWORD = "movdemo123"

random.seed(42)  # deterministic demo data


class Command(BaseCommand):
    help = "Seed demonstration data."

    def add_arguments(self, parser):
        parser.add_argument("--if-empty", action="store_true", help="Skip if demo user exists.")
        parser.add_argument("--flush", action="store_true", help="Delete demo user first.")

    def handle(self, *args, **opts):
        if opts["flush"]:
            User.objects.filter(email=DEMO_EMAIL).delete()
            self.stdout.write("Deleted existing demo user.")

        if opts["if_empty"] and User.objects.filter(email=DEMO_EMAIL).exists():
            self.stdout.write("Demo user already exists; skipping (--if-empty).")
            return

        user, created = User.objects.get_or_create(
            email=DEMO_EMAIL,
            defaults={"full_name": "Demo User", "timezone": "UTC"},
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        if not created:
            # Clean slate for this user's content so reseeding is idempotent.
            for model in (Project, Task, Habit, Note, CalendarEvent, FocusSession, Person, Link, Notification):
                model.objects.filter(owner=user).delete()

        self.stdout.write("Seeding projects, tasks, habits, notes...")
        projects = self._seed_projects(user)
        self._seed_tasks(user, projects)
        self._seed_habits(user)
        self._seed_notes(user, projects)
        self._seed_calendar(user, projects)
        self._seed_focus(user)
        people = self._seed_people(user)
        self._seed_links(user, projects, people)
        self._seed_notifications(user)

        update_profile_snapshot(user)
        build_retrospective(user)
        build_retrospective(user, week_start=timezone.localdate() - timedelta(days=7) - timedelta(days=timezone.localdate().weekday()))

        self.stdout.write(self.style.SUCCESS(f"Done. Login with {DEMO_EMAIL} / {DEMO_PASSWORD}"))

    # ------------------------------------------------------------------ #
    def _seed_projects(self, user):
        specs = [
            ("Website Redesign", "Refresh the marketing site with a new brand.", "#6366f1", "active"),
            ("Mobile App Launch", "Ship v1 of the iOS and Android apps.", "#ec4899", "active"),
            ("Q3 Research", "Customer discovery and market analysis.", "#10b981", "active"),
            ("Personal Growth", "Reading, courses and skill building.", "#f59e0b", "on_hold"),
        ]
        projects = []
        for name, desc, color, status in specs:
            projects.append(
                Project.objects.create(
                    owner=user,
                    name=name,
                    description=desc,
                    color=color,
                    status=status,
                    due_date=timezone.localdate() + timedelta(days=random.randint(20, 90)),
                    is_favorite=random.random() < 0.4,
                )
            )
        return projects

    def _seed_tasks(self, user, projects):
        titles = [
            "Design new homepage hero", "Implement authentication flow",
            "Write onboarding emails", "Research competitor pricing",
            "Build analytics dashboard", "Fix mobile navigation bug",
            "Draft Q3 OKRs", "Set up CI pipeline", "Plan launch event",
            "Review API documentation", "Optimize image loading",
            "Conduct 5 user interviews", "Create design system tokens",
            "Migrate database schema", "Write blog post on momentum",
        ]
        now = timezone.now()
        for i, title in enumerate(titles):
            project = random.choice(projects)
            status = random.choices(
                ["todo", "in_progress", "blocked", "done"], weights=[4, 3, 1, 4]
            )[0]
            created = now - timedelta(days=random.randint(1, 50))
            due = now + timedelta(days=random.randint(-5, 21))
            task = Task.objects.create(
                owner=user,
                project=project,
                title=title,
                description=f"Auto-seeded task: {title.lower()}.",
                status=status,
                importance=random.randint(2, 5),
                urgency=random.randint(1, 5),
                estimated_minutes=random.choice([30, 45, 60, 90, 120]),
                due_date=due,
                created_at=created,
                tags=random.sample(["frontend", "backend", "design", "research", "writing"], k=random.randint(0, 2)),
            )
            # Backdate created_at (auto_now_add ignores it on create).
            Task.objects.filter(pk=task.pk).update(created_at=created)
            if status == "done":
                completed = created + timedelta(days=random.randint(1, 10))
                Task.objects.filter(pk=task.pk).update(
                    completed_at=completed, started_at=created + timedelta(hours=2)
                )
            # Decompose some tasks into subtasks.
            if i % 2 == 0:
                for proposal in decompose(title)[: random.randint(2, 4)]:
                    Subtask.objects.create(
                        task=task,
                        is_done=(status == "done") or random.random() < 0.4,
                        **proposal,
                    )

    def _seed_habits(self, user):
        specs = [
            ("Morning planning", "daily", "#6366f1", "sunrise"),
            ("Deep work block", "daily", "#10b981", "brain"),
            ("Exercise", "daily", "#ef4444", "activity"),
            ("Weekly review", "weekly", "#f59e0b", "calendar"),
        ]
        today = timezone.localdate()
        for name, cadence, color, icon in specs:
            habit = Habit.objects.create(
                owner=user, name=name, cadence=cadence, color=color, icon=icon,
                target_per_period=1 if cadence == "daily" else 1,
            )
            # Create a believable, slightly-imperfect history.
            span = 45 if cadence == "daily" else 56
            for offset in range(span):
                day = today - timedelta(days=offset)
                if cadence == "weekly" and day.weekday() != 6:
                    continue
                if random.random() < (0.8 if cadence == "daily" else 0.7):
                    HabitLog.objects.get_or_create(habit=habit, date=day)

    def _seed_notes(self, user, projects):
        notes = [
            ("Launch checklist", "- [ ] Press kit\n- [ ] App store listing\n- [ ] Beta feedback"),
            ("Interview insights", "Users want faster onboarding and clearer pricing."),
            ("Brand voice", "Confident, warm, never condescending."),
            ("Ideas backlog", "Dark mode, offline sync, Slack integration."),
        ]
        for title, content in notes:
            Note.objects.create(
                owner=user, project=random.choice(projects), title=title,
                content=content, is_pinned=random.random() < 0.3,
                tags=random.sample(["idea", "research", "launch"], k=1),
            )

    def _seed_calendar(self, user, projects):
        now = timezone.now()
        for offset in range(-3, 10):
            day = now + timedelta(days=offset)
            if random.random() < 0.6:
                start = day.replace(hour=random.randint(9, 15), minute=0, second=0, microsecond=0)
                CalendarEvent.objects.create(
                    owner=user,
                    title=random.choice(["Team sync", "Focus block", "Design review", "1:1", "Planning"]),
                    kind=random.choice(["meeting", "focus_block", "event"]),
                    start=start,
                    end=start + timedelta(hours=1),
                    project=random.choice(projects),
                    color=random.choice(["#6366f1", "#10b981", "#ec4899"]),
                )

    def _seed_focus(self, user):
        now = timezone.now()
        for offset in range(45):
            day = now - timedelta(days=offset)
            # Most days have 0-3 focus sessions; weekends lighter.
            n = random.choices([0, 1, 2, 3], weights=[2, 3, 3, 2])[0]
            if day.weekday() >= 5:
                n = max(0, n - 1)
            for _ in range(n):
                hour = random.choice([9, 10, 11, 14, 15, 16, 21])
                start = day.replace(hour=hour, minute=0, second=0, microsecond=0)
                planned = random.choice([25, 50, 90])
                FocusSession.objects.create(
                    owner=user,
                    label=random.choice(["Deep work", "Writing", "Coding", "Design", "Research"]),
                    started_at=start,
                    ended_at=start + timedelta(minutes=planned),
                    planned_minutes=planned,
                    actual_minutes=max(10, planned - random.randint(0, 15)),
                    interruptions=random.randint(0, 4),
                    quality=random.randint(2, 5),
                )

    def _seed_people(self, user):
        specs = [
            ("Alex Rivera", "Designer"),
            ("Jordan Lee", "Engineer"),
            ("Sam Patel", "Product Manager"),
        ]
        return [Person.objects.create(owner=user, name=n, role=r) for n, r in specs]

    def _seed_links(self, user, projects, people):
        # Connect a couple of people to projects in the knowledge graph.
        for person in people:
            project = random.choice(projects)
            Link.objects.get_or_create(
                owner=user,
                source_type="person",
                source_id=person.id,
                target_type="project",
                target_id=project.id,
                relation="works_on",
            )

    def _seed_notifications(self, user):
        Notification.objects.create(
            owner=user, level="insight", title="You're most productive at 10:00",
            body="Consider scheduling deep work in the morning.", link="/intelligence",
        )
        Notification.objects.create(
            owner=user, level="warning", title="2 tasks are overdue",
            body="Review your task list to stay on track.", link="/tasks",
        )
        Notification.objects.create(
            owner=user, level="success", title="Weekly retrospective ready",
            body="Your productivity summary for last week is available.", link="/retrospectives",
        )
