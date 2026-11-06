import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.utils import child_required
from progress.models import Attempt

from . import plan as lesson_plan
from .models import Emotion, Exercise, Level, ReadingLine
from .selection import (
    AttemptInfo, ExerciseInfo, emotion_mastery, pick_exercises, weak_exercises,
)

SESSION_SIZE = 5  # скільки вправ у одному занятті

# Які шаблони показують які типи вправ. Новий тип = новий рядок + новий шаблон.
EXERCISE_TEMPLATES = {
    Exercise.Type.FACE_TO_EMOTION: "lessons/exercises/face.html",
    Exercise.Type.NOVEL: "lessons/exercises/novel.html",
    Exercise.Type.READ_ALOUD: "lessons/exercises/read_aloud.html",
}
SUPPORTED_TYPES = list(EXERCISE_TEMPLATES)

MASTERY_LABELS = ["ще не пробували", "починаємо", "виходить", "добре знаємо"]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]


# ---------- допоміжне ----------

def _load_history(child):
    """Вправи й спроби дитини у вигляді простих даних для selection.py."""
    exercises = Exercise.objects.filter(type__in=SUPPORTED_TYPES).select_related("level")
    # Вправу на читання без жодного речення в заняття не беремо.
    with_lines = set(ReadingLine.objects.values_list("exercise_id", flat=True))
    infos = [
        ExerciseInfo(e.id, e.level.order, e.order, e.emotion_id)
        for e in exercises
        if e.type != Exercise.Type.READ_ALOUD or e.id in with_lines
    ]
    rows = Attempt.objects.filter(child=child).values_list("exercise_id", "is_correct", "created_at")
    attempts = [AttemptInfo(*row) for row in rows]
    return infos, attempts


def _emotion_rows(infos, attempts):
    """Емоції з рівнем освоєння (для головної й статистики)."""
    mastery = emotion_mastery(infos, attempts)
    emotion_of = {e.id: e.emotion_id for e in infos}
    counts = {}
    for attempt in attempts:
        emotion_id = emotion_of.get(attempt.exercise_id)
        if emotion_id is not None:
            counts[emotion_id] = counts.get(emotion_id, 0) + 1

    rows = []
    for emotion in Emotion.objects.order_by("id"):
        level = mastery.get(emotion.id, 0)
        rows.append({
            "emotion": emotion,
            "color": emotion.display_color,
            "dots": [i < level for i in range(3)],
            "label": MASTERY_LABELS[level],
            "attempts": counts.get(emotion.id, 0),
        })
    return rows


def _next_context(plan, exercise):
    """Яка вправа наступна: у занятті за планом, поза заняттям у межах рівня."""
    in_session = bool(plan) and exercise.id in plan["ids"]
    if in_session:
        next_id = lesson_plan.next_id(plan, exercise.id)
        next_exercise = Exercise.objects.filter(id=next_id).first() if next_id else None
    else:
        next_exercise = Exercise.objects.filter(
            level=exercise.level, order__gt=exercise.order
        ).first()
    return {"next_exercise": next_exercise, "in_session": in_session}


def _with_step_header(response, plan, exercise_id):
    """Повідомляє сторінці, який крок заняття щойно завершено (для смужки)."""
    index = lesson_plan.step_index(plan, exercise_id)
    if index is not None:
        response["X-Step-Index"] = str(index)
    return response


# ---------- головна й заняття ----------

@login_required
@child_required
def home(request):
    child = request.child
    plan = lesson_plan.get(request, child)
    resume_id = lesson_plan.first_undone(plan) if plan else None

    infos, attempts = _load_history(child)
    emotions = _emotion_rows(infos, attempts)

    return render(request, "lessons/home.html", {
        "child": child,
        "resume_id": resume_id,
        "session_size": SESSION_SIZE,
        "emotions": emotions,
    })


@login_required
@child_required
@require_POST
def session_start(request):
    infos, attempts = _load_history(request.child)
    ids = pick_exercises(infos, attempts, n=SESSION_SIZE, now=timezone.now())
    if not ids:
        messages.info(request, "Вправ поки немає. Їх можна додати в адмінці.")
        return redirect("lessons:home")
    lesson_plan.start(request, request.child, ids)
    return redirect("lessons:exercise_detail", id=ids[0])


@login_required
@child_required
def session_resume(request):
    plan = lesson_plan.get(request, request.child)
    next_id = lesson_plan.first_undone(plan) if plan else None
    if next_id:
        return redirect("lessons:exercise_detail", id=next_id)
    return redirect("lessons:home")


@login_required
@child_required
def session_done(request):
    plan = lesson_plan.get(request, request.child)
    if not plan:
        return redirect("lessons:home")
    unfinished = lesson_plan.first_undone(plan)
    if unfinished:
        return redirect("lessons:exercise_detail", id=unfinished)

    started = datetime.fromisoformat(plan["started"])
    attempts = Attempt.objects.filter(
        child=request.child, exercise_id__in=plan["ids"], created_at__gte=started
    ).order_by("created_at")
    first_results = {}
    for attempt in attempts:
        first_results.setdefault(attempt.exercise_id, attempt.is_correct)

    return render(request, "lessons/session_done.html", {
        "child": request.child,
        "total": len(plan["ids"]),
        "first_try": sum(1 for ok in first_results.values() if ok),
    })


# ---------- перелік усіх вправ і статистика ----------

@login_required
@child_required
def level_list(request):
    levels = list(Level.objects.prefetch_related(
        Prefetch(
            "exercises",
            queryset=Exercise.objects.filter(type__in=SUPPORTED_TYPES).select_related("emotion"),
        )
    ))

    # Підсумок спроб дитини по кожній вправі для розкривних відомостей.
    summary = {}
    rows = Attempt.objects.filter(child=request.child).order_by("created_at")
    for exercise_id, is_correct, created_at in rows.values_list(
        "exercise_id", "is_correct", "created_at"
    ):
        item = summary.setdefault(exercise_id, {"attempts": 0, "correct": 0})
        item["attempts"] += 1
        item["correct"] += 1 if is_correct else 0
        item["last_at"] = created_at

    for level in levels:
        for exercise in level.exercises.all():
            item = summary.get(exercise.id, {})
            exercise.attempts_count = item.get("attempts", 0)
            exercise.correct_count = item.get("correct", 0)
            exercise.last_at = item.get("last_at")

    return render(request, "lessons/level_list.html", {"levels": levels})


@login_required
@child_required
def stats(request):
    child = request.child
    infos, attempts = _load_history(child)
    known = {e.id for e in infos}

    total_attempts = len(attempts)
    correct = sum(1 for a in attempts if a.is_correct)
    tried = len({a.exercise_id for a in attempts if a.exercise_id in known})

    # активність за останні 7 днів
    today = timezone.localdate()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    counts = dict.fromkeys(days, 0)
    for attempt in attempts:
        day = timezone.localtime(attempt.created_at).date()
        if day in counts:
            counts[day] += 1
    peak = max(counts.values()) or 1
    week = [
        {
            "label": WEEKDAYS[day.weekday()],
            "count": counts[day],
            "height": max(10, round(100 * counts[day] / peak)) if counts[day] else 0,
            "today": day == today,
        }
        for day in days
    ]

    weak_ids = weak_exercises(infos, attempts, limit=3)
    by_id = {
        e.id: e
        for e in Exercise.objects.filter(id__in=weak_ids).select_related("level", "emotion")
    }

    return render(request, "lessons/stats.html", {
        "child": child,
        "total_attempts": total_attempts,
        "tried": tried,
        "total_exercises": len(infos),
        "percent_ok": round(100 * correct / total_attempts) if total_attempts else 0,
        "week": week,
        "emotions": _emotion_rows(infos, attempts),
        "weak": [by_id[i] for i in weak_ids if i in by_id],
    })


# ---------- вправи ----------

@login_required
@child_required
def exercise_detail(request, id):
    exercise = get_object_or_404(Exercise, id=id)
    template = EXERCISE_TEMPLATES.get(exercise.type, "lessons/exercises/unsupported.html")
    plan = lesson_plan.get(request, request.child)
    context = {
        "exercise": exercise,
        "progress": lesson_plan.progress(plan, exercise.id) if plan else None,
    }
    if exercise.type == Exercise.Type.NOVEL:
        context["novel_url"] = f"{settings.MEDIA_URL}{exercise.data.get('build', '')}"
    if exercise.type == Exercise.Type.READ_ALOUD:
        context["lines"] = list(exercise.lines.select_related("emotion"))
        context["show_text"] = request.child.can_read
    return render(request, template, context)


@login_required
@child_required
@require_POST
def exercise_answer(request, id):
    exercise = get_object_or_404(Exercise, id=id, type=Exercise.Type.FACE_TO_EMOTION)
    chosen = request.POST.get("choice")

    if chosen not in exercise.data.get("options", []):
        return HttpResponseBadRequest("Невідомий варіант відповіді")

    correct = exercise.data.get("correct")
    is_correct = chosen == correct

    Attempt.objects.create(
        child=request.child, exercise=exercise,
        answer={"chosen": chosen}, is_correct=is_correct,
    )
    plan = lesson_plan.mark_done(request, request.child, exercise.id)

    response = render(request, "lessons/partials/feedback.html", {
        "is_correct": is_correct,
        "correct": correct,
        "explanation": exercise.data.get("explanation", ""),
        **_next_context(plan, exercise),
    })
    return _with_step_header(response, plan, exercise.id)


@login_required
@child_required
@require_POST
def novel_result(request, id):
    exercise = get_object_or_404(Exercise, id=id, type=Exercise.Type.NOVEL)
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Некоректні дані")
    if not isinstance(payload, dict):
        return HttpResponseBadRequest("Некоректні дані")

    fits = payload.get("fits") is True

    Attempt.objects.create(
        child=request.child, exercise=exercise, answer=payload, is_correct=fits,
    )

    plan = lesson_plan.get(request, request.child)
    if fits:  # крок вважається пройденим, коли знайдено доречну реакцію
        plan = lesson_plan.mark_done(request, request.child, exercise.id)

    response = render(request, "lessons/partials/novel_feedback.html", {
        "fits": fits,
        **_next_context(plan, exercise),
    })
    return _with_step_header(response, plan, exercise.id) if fits else response


@login_required
@child_required
@require_POST
def reading_result(request, id):
    """Підсумок вправи на виразне читання. Записів голосу ми не отримуємо й не зберігаємо."""
    exercise = get_object_or_404(Exercise, id=id, type=Exercise.Type.READ_ALOUD)
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Некоректні дані")
    if not isinstance(payload, dict):
        return HttpResponseBadRequest("Некоректні дані")

    def count(key):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000:
            return None
        return value

    lines_done, replays, recorded = count("lines_done"), count("replays"), count("recorded")
    if None in (lines_done, replays, recorded):
        return HttpResponseBadRequest("Некоректні дані")

    total = exercise.lines.count()
    lines_done = min(lines_done, total)

    # Оцінки «правильно/неправильно» тут немає: спроба фіксує лише участь.
    Attempt.objects.create(
        child=request.child, exercise=exercise,
        answer={"lines_done": lines_done, "replays": replays, "recorded": recorded},
        is_correct=True,
    )
    plan = lesson_plan.mark_done(request, request.child, exercise.id)

    response = render(request, "lessons/partials/reading_feedback.html", {
        "lines_done": lines_done,
        "total": total,
        **_next_context(plan, exercise),
    })
    return _with_step_header(response, plan, exercise.id)
