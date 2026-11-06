"""Автоматичний добір вправ для дитини.

Модуль навмисно не залежить від Django: він приймає прості дані (вправи й
спроби) і повертає список id вправ. Тому його легко тестувати й змінювати.

Як це працює
------------
1. Рівні відкриваються поступово: доступні всі рівні, у яких дитина вже
   спробувала кожну вправу, плюс перший рівень, де ще є нові вправи.
2. Початківець (менше BEGINNER_ATTEMPTS спроб): спокійний старт, нові вправи
   по порядку, без повторень.
3. Досвідчена дитина: частина заняття це повторення вправ, які даються
   важче (за останніми спробами та за емоцією) або давно не повторювалися,
   решта це нові вправи. Вправу, яку дитина щойно робила, одразу не повторюємо.
4. Усередині заняття вправи йдуть у порядку програми: спочатку знайоме
   (повторення з попередніх рівнів), потім нове.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence

BEGINNER_ATTEMPTS = 5            # менше спроб: дитина вважається початківцем
RECENT_WINDOW = 5                # скільки останніх спроб враховуємо для вправи
EMOTION_WINDOW = 10              # ... і для емоції
EMOTION_MIN_ATTEMPTS = 3         # менше спроб: про емоцію ще рано робити висновки
REPEAT_COOLDOWN = timedelta(hours=1)   # щойно зроблену вправу не повторюємо
REVIEW_SHARE = 0.4               # частка повторення в занятті досвідченої дитини
MIN_REVIEW_SCORE = 0.5           # повторюємо лише те, що справді варто


@dataclass(frozen=True)
class ExerciseInfo:
    id: int
    level_order: int
    order: int
    emotion_id: Optional[int] = None


@dataclass(frozen=True)
class AttemptInfo:
    exercise_id: int
    is_correct: bool
    created_at: datetime


def _weighted_accuracy(attempts: Sequence[AttemptInfo], window: int) -> Optional[float]:
    """Частка вдалих спроб серед останніх; свіжіші спроби важать більше."""
    recent = sorted(attempts, key=lambda a: a.created_at)[-window:]
    if not recent:
        return None
    weights = range(1, len(recent) + 1)
    total = sum(weights)
    return sum(w for w, a in zip(weights, recent) if a.is_correct) / total


def _curriculum_key(exercise: ExerciseInfo):
    return (exercise.level_order, exercise.order, exercise.id)


def _unlocked(ordered: Sequence[ExerciseInfo],
              by_exercise: Dict[int, List[AttemptInfo]]) -> List[ExerciseInfo]:
    """Вправи доступних рівнів (див. пункт 1 у описі модуля)."""
    levels: List[List[ExerciseInfo]] = []
    for exercise in ordered:
        if not levels or levels[-1][0].level_order != exercise.level_order:
            levels.append([])
        levels[-1].append(exercise)

    result: List[ExerciseInfo] = []
    for items in levels:
        result.extend(items)
        if any(e.id not in by_exercise for e in items):
            break  # далі рівні поки закриті
    return result


def _emotion_accuracy(exercises: Sequence[ExerciseInfo],
                      by_exercise: Dict[int, List[AttemptInfo]]) -> Dict[int, float]:
    emotion_of = {e.id: e.emotion_id for e in exercises if e.emotion_id is not None}
    groups: Dict[int, List[AttemptInfo]] = {}
    for exercise_id, items in by_exercise.items():
        emotion_id = emotion_of.get(exercise_id)
        if emotion_id is not None:
            groups.setdefault(emotion_id, []).extend(items)
    return {
        emotion_id: _weighted_accuracy(items, EMOTION_WINDOW)
        for emotion_id, items in groups.items()
        if len(items) >= EMOTION_MIN_ATTEMPTS
    }


def emotion_mastery(exercises: Sequence[ExerciseInfo],
                    attempts: Sequence[AttemptInfo]) -> Dict[int, int]:
    """Рівень знайомства з емоцією: 0 (не пробували) ... 3 (добре знаємо)."""
    emotion_of = {e.id: e.emotion_id for e in exercises if e.emotion_id is not None}
    groups: Dict[int, List[AttemptInfo]] = {}
    for attempt in attempts:
        emotion_id = emotion_of.get(attempt.exercise_id)
        if emotion_id is not None:
            groups.setdefault(emotion_id, []).append(attempt)

    result: Dict[int, int] = {}
    for emotion_id, items in groups.items():
        if len(items) < 2:
            result[emotion_id] = 1
            continue
        accuracy = _weighted_accuracy(items, EMOTION_WINDOW)
        result[emotion_id] = 3 if accuracy >= 0.8 else 2 if accuracy >= 0.5 else 1
    return result


def pick_exercises(exercises: Sequence[ExerciseInfo],
                   attempts: Sequence[AttemptInfo],
                   n: int,
                   now: datetime,
                   rng: Optional[random.Random] = None) -> List[int]:
    """Повертає до n id вправ для нового заняття."""
    rng = rng or random.Random()
    ordered = sorted(exercises, key=_curriculum_key)
    if not ordered or n <= 0:
        return []

    known = {e.id for e in ordered}
    by_exercise: Dict[int, List[AttemptInfo]] = {}
    for attempt in attempts:
        if attempt.exercise_id in known:
            by_exercise.setdefault(attempt.exercise_id, []).append(attempt)

    candidates = _unlocked(ordered, by_exercise)
    total_attempts = sum(len(items) for items in by_exercise.values())

    if total_attempts < BEGINNER_ATTEMPTS:
        unseen = [e for e in candidates if e.id not in by_exercise]
        seen = [e for e in candidates if e.id in by_exercise]
        chosen = (unseen + seen)[:n]
        return [e.id for e in sorted(chosen, key=_curriculum_key)]

    emotion_accuracy = _emotion_accuracy(ordered, by_exercise)
    new: List[ExerciseInfo] = []
    ready = []     # (оцінка, вправа): можна повторювати
    cooling = []   # щойно робили: у крайньому разі наприкінці
    for exercise in candidates:
        history = by_exercise.get(exercise.id)
        if not history:
            new.append(exercise)
            continue
        age = now - max(a.created_at for a in history)
        weakness = 1.0 - _weighted_accuracy(history, RECENT_WINDOW)
        staleness = min(age.total_seconds() / 86400, 7.0) / 7.0
        emotion_weakness = 0.0
        if exercise.emotion_id in emotion_accuracy:
            emotion_weakness = 1.0 - emotion_accuracy[exercise.emotion_id]
        score = (2.0 * weakness + 0.5 * staleness + 0.5 * emotion_weakness
                 + rng.uniform(0.0, 0.2))
        (cooling if age < REPEAT_COOLDOWN else ready).append((score, exercise))

    ready.sort(key=lambda item: -item[0])
    cooling.sort(key=lambda item: -item[0])

    want_review = int(n * REVIEW_SHARE + 0.5)
    chosen: List[ExerciseInfo] = [
        e for score, e in ready if score >= MIN_REVIEW_SCORE
    ][:want_review]

    for exercise in new:
        if len(chosen) >= n:
            break
        chosen.append(exercise)

    for _, exercise in ready + cooling:   # якщо нових замало, добираємо повторенням
        if len(chosen) >= n:
            break
        if exercise not in chosen:
            chosen.append(exercise)

    return [e.id for e in sorted(chosen, key=_curriculum_key)]


def weak_exercises(exercises: Sequence[ExerciseInfo],
                   attempts: Sequence[AttemptInfo],
                   limit: int = 3) -> List[int]:
    """id вправ, які варто повторити: щонайменше 2 спроби й точність нижче 60%."""
    known = {e.id for e in exercises}
    by_exercise: Dict[int, List[AttemptInfo]] = {}
    for attempt in attempts:
        if attempt.exercise_id in known:
            by_exercise.setdefault(attempt.exercise_id, []).append(attempt)

    scored = []
    for exercise_id, items in by_exercise.items():
        if len(items) < 2:
            continue
        accuracy = _weighted_accuracy(items, RECENT_WINDOW)
        if accuracy < 0.6:
            scored.append((accuracy, exercise_id))
    scored.sort()
    return [exercise_id for _, exercise_id in scored[:limit]]
