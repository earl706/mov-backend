"""Unified search across the user's entities.

A single GET /api/search/?q=... returns grouped, ranked results from tasks,
notes, projects, habits and people. For a prototype this uses icontains; a
production build would back this with PostgreSQL full-text search or an external
index, but the response contract would be unchanged.
"""
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.habits.models import Habit
from apps.knowledge.models import Person
from apps.notes.models import Note
from apps.projects.models import Project
from apps.tasks.models import Task

LIMIT_PER_GROUP = 8


class SearchView(APIView):
    @extend_schema(
        parameters=[OpenApiParameter("q", str, description="Search query")],
        responses={200: dict},
    )
    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response({"query": q, "groups": []})

        user = request.user
        groups = []

        tasks = Task.objects.filter(owner=user).filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )[:LIMIT_PER_GROUP]
        groups.append(
            {
                "type": "task",
                "label": "Tasks",
                "results": [
                    {"id": t.id, "uuid": str(t.uuid), "title": t.title, "subtitle": t.status}
                    for t in tasks
                ],
            }
        )

        notes = Note.objects.filter(owner=user).filter(
            Q(title__icontains=q) | Q(content__icontains=q)
        )[:LIMIT_PER_GROUP]
        groups.append(
            {
                "type": "note",
                "label": "Notes",
                "results": [
                    {"id": n.id, "uuid": str(n.uuid), "title": n.title, "subtitle": ""}
                    for n in notes
                ],
            }
        )

        projects = Project.objects.filter(owner=user).filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )[:LIMIT_PER_GROUP]
        groups.append(
            {
                "type": "project",
                "label": "Projects",
                "results": [
                    {"id": p.id, "uuid": str(p.uuid), "title": p.name, "subtitle": p.status}
                    for p in projects
                ],
            }
        )

        habits = Habit.objects.filter(owner=user, name__icontains=q)[:LIMIT_PER_GROUP]
        groups.append(
            {
                "type": "habit",
                "label": "Habits",
                "results": [
                    {"id": h.id, "uuid": str(h.uuid), "title": h.name, "subtitle": h.cadence}
                    for h in habits
                ],
            }
        )

        people = Person.objects.filter(owner=user).filter(
            Q(name__icontains=q) | Q(role__icontains=q)
        )[:LIMIT_PER_GROUP]
        groups.append(
            {
                "type": "person",
                "label": "People",
                "results": [
                    {"id": p.id, "uuid": str(p.uuid), "title": p.name, "subtitle": p.role}
                    for p in people
                ],
            }
        )

        total = sum(len(g["results"]) for g in groups)
        return Response({"query": q, "total": total, "groups": [g for g in groups if g["results"]]})
