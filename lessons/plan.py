"""Заняття (сеанс): послідовність вправ, що зберігається в сесії користувача."""
from __future__ import annotations

from django.utils import timezone

SESSION_KEY = "lesson_plan"


def start(request, child, exercise_ids):
    request.session[SESSION_KEY] = {
        "child_id": child.id,
        "ids": list(exercise_ids),
        "done": [],
        "started": timezone.now().isoformat(),
    }


def get(request, child):
    """Активне заняття цієї дитини або None."""
    plan = request.session.get(SESSION_KEY)
    if not plan or plan.get("child_id") != child.id:
        return None
    return plan


def mark_done(request, child, exercise_id):
    plan = get(request, child)
    if plan and exercise_id in plan["ids"] and exercise_id not in plan["done"]:
        plan["done"].append(exercise_id)
        request.session.modified = True
    return plan


def first_undone(plan):
    return next((i for i in plan["ids"] if i not in plan["done"]), None)


def next_id(plan, current_id):
    ids = plan["ids"]
    if current_id not in ids:
        return None
    index = ids.index(current_id)
    return ids[index + 1] if index + 1 < len(ids) else None


def step_index(plan, exercise_id):
    if plan and exercise_id in plan["ids"]:
        return plan["ids"].index(exercise_id)
    return None


def progress(plan, current_id):
    """Дані для смужки кроків або None, якщо вправа не входить до заняття."""
    index = step_index(plan, current_id)
    if index is None:
        return None
    steps = [
        {"done": i in plan["done"], "current": i == current_id and i not in plan["done"]}
        for i in plan["ids"]
    ]
    return {"total": len(plan["ids"]), "current": index + 1, "steps": steps}
