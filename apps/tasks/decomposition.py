"""AI-assisted task decomposition.

A production deployment would call an LLM here. To keep the prototype fully
self-contained and deterministic (and testable without network/keys), this uses
a heuristic "planner" that recognises common task archetypes from the title and
description and emits a sensible subtask checklist. The interface
(`decompose(title, description)` -> list[dict]) is identical to what an LLM-backed
implementation would expose, so swapping it out later is a one-line change.
"""
import re

# Archetype -> ordered checklist. Keyed by trigger keywords found in the task.
_TEMPLATES = {
    ("write", "draft", "blog", "article", "essay", "post"): [
        ("Outline key points and structure", 20),
        ("Write first draft", 45),
        ("Revise for clarity and flow", 30),
        ("Proofread and finalize", 15),
    ],
    ("design", "mockup", "wireframe", "ui", "ux"): [
        ("Gather references and requirements", 20),
        ("Sketch low-fidelity layout", 30),
        ("Produce high-fidelity design", 45),
        ("Collect feedback and iterate", 30),
    ],
    ("build", "implement", "develop", "feature", "code", "api"): [
        ("Clarify requirements and acceptance criteria", 20),
        ("Design the approach / data model", 30),
        ("Implement core logic", 60),
        ("Write tests", 30),
        ("Review, refactor and document", 25),
    ],
    ("research", "investigate", "explore", "analyze"): [
        ("Define the questions to answer", 15),
        ("Collect sources and data", 40),
        ("Synthesize findings", 30),
        ("Summarize and recommend next steps", 20),
    ],
    ("plan", "organize", "prepare", "event", "meeting"): [
        ("List goals and constraints", 15),
        ("Draft the agenda / schedule", 25),
        ("Coordinate with stakeholders", 30),
        ("Confirm logistics and follow up", 20),
    ],
}

_GENERIC = [
    ("Break down what 'done' looks like", 15),
    ("Do the main work", 40),
    ("Review the result", 20),
    ("Wrap up and capture follow-ups", 10),
]


def decompose(title, description=""):
    """Return a list of {title, estimated_minutes, ai_generated} subtasks."""
    text = f"{title} {description}".lower()
    words = set(re.findall(r"[a-z]+", text))

    chosen = None
    for triggers, template in _TEMPLATES.items():
        if words & set(triggers):
            chosen = template
            break
    template = chosen or _GENERIC

    return [
        {"title": sub_title, "estimated_minutes": minutes, "ai_generated": True, "order": i}
        for i, (sub_title, minutes) in enumerate(template)
    ]
