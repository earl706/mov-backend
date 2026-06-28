from apps.habits.models import Habit
from apps.notes.models import Note
from apps.projects.models import Project
from apps.tasks.models import Task

from .models import Link, Person

def _node(node_type, pk, label, extra=None):
    return {"id": f"{node_type}:{pk}", "type": node_type, "label": label, **(extra or {})}

def build_graph(user):
    nodes = {}
    edges = []

    def add(node):
        nodes[node["id"]] = node

    projects = list(Project.objects.filter(owner=user))
    tasks = list(Task.objects.filter(owner=user).select_related("project"))
    notes = list(Note.objects.filter(owner=user).select_related("project", "task"))
    habits = list(Habit.objects.filter(owner=user))
    people = list(Person.objects.filter(owner=user))

    for p in projects:
        add(_node("project", p.id, p.name, {"color": p.color}))
    for t in tasks:
        add(_node("task", t.id, t.title, {"status": t.status}))
        if t.project_id:
            edges.append({"source": f"task:{t.id}", "target": f"project:{t.project_id}", "relation": "belongs_to"})
    for n in notes:
        add(_node("note", n.id, n.title))
        if n.project_id:
            edges.append({"source": f"note:{n.id}", "target": f"project:{n.project_id}", "relation": "documents"})
        if n.task_id:
            edges.append({"source": f"note:{n.id}", "target": f"task:{n.task_id}", "relation": "documents"})
    for h in habits:
        add(_node("habit", h.id, h.name, {"color": h.color}))
    for person in people:
        add(_node("person", person.id, person.name, {"role": person.role}))


    for link in Link.objects.filter(owner=user):
        edges.append(
            {
                "source": f"{link.source_type}:{link.source_id}",
                "target": f"{link.target_type}:{link.target_id}",
                "relation": link.relation,
            }
        )


    valid = [e for e in edges if e["source"] in nodes and e["target"] in nodes]
    return {"nodes": list(nodes.values()), "edges": valid}
