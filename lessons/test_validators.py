import unittest

from lessons.validators import validate_exercise_data as check

FACE = [
    {"options": ["страх", "радість", "злість"], "correct": "страх", "explanation": "..."},
    {"options": ["сум", "сором", "злість"], "correct": "сором", "explanation": "..."},
    {"options": ["гордість", "радість", "спокій"], "correct": "гордість", "explanation": "..."},
]
SITUATION = [
    {"situation": "На вулиці гучно гримить грім. Марко сидить сам у кімнаті й чує кожен удар.",
     "options": ["страх", "радість", "злість"], "correct": "страх", "explanation": "..."},
    {"situation": "Софійка розлила сік на скатертину.", "options": ["сором", "радість", "сум"],
     "correct": "сором", "explanation": "..."},
    {"situation": "Марко сам зібрав великий пазл.", "options": ["гордість", "страх", "сором"],
     "correct": "гордість", "explanation": "..."},
]


def phrase(situation, good, bad1, bad2):
    return {"situation": situation, "options": [
        {"text": good[0], "fits": True, "feedback": good[1]},
        {"text": bad1[0], "fits": False, "feedback": bad1[1]},
        {"text": bad2[0], "fits": False, "feedback": bad2[1]},
    ]}


PHRASE = [
    phrase("На вулиці гроза, і тобі страшно. Мама поруч.", ("Мамо, мені страшно. Побудь, будь ласка, зі мною.", "Так."),
           ("Нічого не кажу й ховаюся під ковдру.", "Ця фраза не зовсім підходить."), ("Я зовсім не боюся, це дурниці!", "Не зовсім підходить.")),
    phrase("Ти випадково розлив(-ла) сік.", ("Вибач, це випадково. Я зараз витру.", "Так."),
           ("Це не я!", "Не зовсім підходить."), ("Мовчки йду до своєї кімнати.", "Втекти хочеться.")),
    phrase("Ти зібрав(-ла) складний пазл.", ("Дивись, що в мене вийшло! Я цим пишаюся.", "Так."),
           ("Це нічого особливого.", "Не зовсім підходить."), ("Я кращий за всіх!", "Не зовсім підходить.")),
]
MATCH = [
    {"pairs": [{"left": "Страх", "right": "Гримить гроза, а ти вдома сам"}, {"left": "Сором", "right": "Усі дивляться, як ти розлив сік"},
               {"left": "Гордість", "right": "Ти сам зібрав складний пазл"}], "explanation": "..."},
    {"pairs": [{"left": "Страх", "right": "Широко розплющені очі"}, {"left": "Сором", "right": "Опущений погляд"},
               {"left": "Гордість", "right": "Підняте підборіддя"}], "explanation": "..."},
    {"pairs": [{"left": "Страх", "right": "Попросити, щоб хтось побув поруч"}, {"left": "Сором", "right": "Сказати «вибач»"},
               {"left": "Гордість", "right": "Розповісти, чим пишаєшся"}], "explanation": "..."},
]
LABELS = ["зовсім ні", "трохи", "помірно", "сильно", "дуже сильно"]
SCALE = [
    {"situation": "Ти почув тихий шурхіт за вікном.", "labels": LABELS, "correct": [1, 2], "explanation": "..."},
    {"situation": "Ти забув вірш перед усім класом.", "labels": LABELS, "correct": [3, 4], "explanation": "..."},
    {"situation": "Ти виграв змагання.", "labels": LABELS, "correct": [4, 5], "explanation": "..."},
]


class ExamplesFromTheGuide(unittest.TestCase):
    def test_all_examples_are_valid(self):
        for kind, items in (("face", FACE), ("situation", SITUATION), ("phrase", PHRASE), ("match", MATCH), ("scale", SCALE)):
            for number, data in enumerate(items, start=1):
                self.assertEqual(check(kind, data), [], f"{kind} #{number}")


class Mistakes(unittest.TestCase):
    def test_not_an_object(self):
        self.assertTrue(check("face", ["a", "b"]))

    def test_correct_must_match_options(self):
        self.assertTrue(check("face", {"options": ["сум", "сором"], "correct": "Сором"}))

    def test_situation_required(self):
        self.assertTrue(check("situation", {"options": ["a", "b"], "correct": "a"}))

    def test_phrase_needs_a_fitting_option_and_boolean(self):
        data = phrase("s", ("a", "x"), ("b", "y"), ("c", "z"))
        data["options"][0]["fits"] = False
        self.assertTrue(check("phrase", data))
        data["options"][0]["fits"] = "true"
        self.assertTrue(any("true або false" in e for e in check("phrase", data)))

    def test_match_needs_unique_sides(self):
        data = {"pairs": [{"left": "A", "right": "x"}, {"left": "A", "right": "y"}]}
        self.assertTrue(check("match", data))
        self.assertTrue(check("match", {"pairs": [{"left": "A", "right": "x"}]}))

    def test_scale_range(self):
        base = {"situation": "s", "labels": LABELS}
        self.assertTrue(check("scale", {**base, "correct": [0, 2]}))
        self.assertTrue(check("scale", {**base, "correct": [6]}))
        self.assertTrue(check("scale", {**base, "correct": []}))
        self.assertTrue(check("scale", {**base, "correct": [True]}))
        self.assertEqual(check("scale", {**base, "correct": [5]}), [])

    def test_novel_and_reading(self):
        self.assertTrue(check("novel", {}))
        self.assertEqual(check("novel", {"build": "novels/radist/index.html"}), [])
        self.assertEqual(check("read_aloud", {}), [])


if __name__ == "__main__":
    unittest.main()
