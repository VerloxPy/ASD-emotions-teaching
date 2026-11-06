import random
import unittest
from datetime import datetime, timedelta, timezone

from lessons.selection import (
    AttemptInfo, ExerciseInfo, emotion_mastery, pick_exercises, weak_exercises,
)

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def ex(id, level, order, emotion=None):
    return ExerciseInfo(id=id, level_order=level, order=order, emotion_id=emotion)


def att(exercise_id, correct, hours_ago):
    return AttemptInfo(exercise_id, correct, NOW - timedelta(hours=hours_ago))


def bank():
    level1 = [ex(i, 1, i, emotion=1) for i in range(1, 7)]        # 1..6
    level2 = [ex(i, 2, i - 6, emotion=2) for i in range(7, 13)]   # 7..12
    return level1 + level2


class BeginnerTests(unittest.TestCase):
    def test_no_history_gets_first_exercises_in_order(self):
        ids = pick_exercises(bank(), [], n=5, now=NOW)
        self.assertEqual(ids, [1, 2, 3, 4, 5])

    def test_few_attempts_prefers_unseen(self):
        history = [att(1, True, 24), att(2, False, 24)]
        ids = pick_exercises(bank(), history, n=4, now=NOW)
        self.assertEqual(ids, [3, 4, 5, 6])

    def test_second_level_is_closed_until_first_is_tried(self):
        history = [att(i, True, 24) for i in range(1, 4)]   # 4..6 ще не пробували
        ids = pick_exercises(bank(), history, n=6, now=NOW)
        self.assertTrue(all(i <= 6 for i in ids))


class ExperiencedTests(unittest.TestCase):
    def history(self):
        # Рівень 1 пройдено 3 дні тому; вправу 1 дитина двічі зробила невдало.
        rows = [att(1, False, 72), att(1, False, 71)]
        rows += [att(i, True, 72) for i in range(2, 7)]
        return rows

    def test_weak_exercise_comes_back_and_new_level_opens(self):
        ids = pick_exercises(bank(), self.history(), n=5, now=NOW, rng=random.Random(1))
        reviews = [i for i in ids if i <= 6]
        new = [i for i in ids if i > 6]
        self.assertEqual(len(ids), 5)
        self.assertIn(1, reviews)                      # найслабша вправа повертається
        self.assertLessEqual(len(reviews), 2)          # повторення не перевищує ~40%
        self.assertEqual(new, list(range(7, 7 + len(new))))   # нове йде по порядку

    def test_just_done_exercise_is_not_repeated_right_away(self):
        history = self.history() + [att(3, False, 0.2)]
        ids = pick_exercises(bank(), history, n=5, now=NOW, rng=random.Random(2))
        self.assertNotIn(3, ids)

    def test_small_bank_returns_everything_without_duplicates(self):
        small = [ex(1, 1, 1, 1), ex(2, 1, 2, 1)]
        history = [att(1, True, 48), att(2, False, 48)] * 3
        ids = pick_exercises(small, history, n=5, now=NOW)
        self.assertEqual(sorted(ids), [1, 2])

    def test_same_seed_same_result(self):
        a = pick_exercises(bank(), self.history(), n=5, now=NOW, rng=random.Random(7))
        b = pick_exercises(bank(), self.history(), n=5, now=NOW, rng=random.Random(7))
        self.assertEqual(a, b)

    def test_session_is_ordered_by_curriculum(self):
        ids = pick_exercises(bank(), self.history(), n=5, now=NOW, rng=random.Random(3))
        self.assertEqual(ids, sorted(ids))


class MasteryTests(unittest.TestCase):
    def test_levels(self):
        exercises = [ex(1, 1, 1, 10), ex(2, 1, 2, 20), ex(3, 1, 3, 30), ex(4, 1, 4, 40)]
        attempts = [
            att(1, True, 5), att(1, True, 4), att(1, True, 3),        # емоція 10: добре
            att(2, True, 6), att(2, True, 5), att(2, False, 4),       # емоція 20: так собі
            att(3, True, 5),                                          # емоція 30: одна спроба
        ]
        result = emotion_mastery(exercises, attempts)
        self.assertEqual(result[10], 3)
        self.assertEqual(result[20], 2)
        self.assertEqual(result[30], 1)
        self.assertNotIn(40, result)   # без спроб: 0 визначає викликач


class WeakTests(unittest.TestCase):
    def test_flags_only_repeatedly_unsuccessful_exercises(self):
        exercises = [ex(1, 1, 1), ex(2, 1, 2), ex(3, 1, 3), ex(4, 1, 4)]
        attempts = [
            att(1, False, 30), att(1, False, 20),                    # слабка: двічі невдало
            att(2, True, 30), att(2, True, 20),                      # добра
            att(3, False, 10),                                       # одна спроба: рано судити
            att(4, False, 30), att(4, False, 20), att(4, True, 10),  # 3/6 = 0.5: варто повторити
        ]
        self.assertEqual(weak_exercises(exercises, attempts), [1, 4])

    def test_limit_and_empty(self):
        self.assertEqual(weak_exercises([], []), [])
        exercises = [ex(i, 1, i) for i in range(1, 6)]
        attempts = [att(i, False, h) for i in range(1, 6) for h in (30, 20)]
        self.assertEqual(len(weak_exercises(exercises, attempts, limit=3)), 3)


if __name__ == "__main__":
    unittest.main()
