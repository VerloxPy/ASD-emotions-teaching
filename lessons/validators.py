from __future__ import annotations


def _text(value):
    return isinstance(value, str) and value.strip() != ""


def _text_list(value, minimum):
    return isinstance(value, list) and len(value) >= minimum and all(_text(v) for v in value)


def _int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _choice_errors(data, needs_situation):
    errors = []
    if needs_situation and not _text(data.get("situation")):
        errors.append("«situation» має бути непорожнім рядком (опис ситуації).")
    options = data.get("options")
    if not _text_list(options, 2):
        errors.append("«options» має бути списком щонайменше з двох непорожніх рядків.")
    correct = data.get("correct")
    if not _text(correct):
        errors.append("«correct» має бути непорожнім рядком.")
    elif _text_list(options, 2) and correct not in options:
        errors.append("Значення «correct» має точно збігатися з одним із «options».")
    return errors


def _phrase_errors(data):
    errors = []
    if not _text(data.get("situation")):
        errors.append("«situation» має бути непорожнім рядком (опис ситуації).")
    options = data.get("options")
    if not isinstance(options, list) or len(options) < 2:
        return errors + ["«options» має бути списком щонайменше з двох фраз."]
    for number, option in enumerate(options, start=1):
        if not isinstance(option, dict):
            errors.append(f"Фраза {number}: має бути об'єктом із полями text, fits, feedback.")
            continue
        if not _text(option.get("text")):
            errors.append(f"Фраза {number}: «text» має бути непорожнім рядком.")
        if not isinstance(option.get("fits"), bool):
            errors.append(f"Фраза {number}: «fits» має бути true або false (без лапок).")
        if not _text(option.get("feedback")):
            errors.append(f"Фраза {number}: «feedback» має бути непорожнім рядком (м'який коментар).")
    if not any(isinstance(o, dict) and o.get("fits") is True for o in options):
        errors.append("Принаймні одна фраза має мати \"fits\": true.")
    return errors


def _match_errors(data):
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or len(pairs) < 2:
        return ["«pairs» має бути списком щонайменше з двох пар."]
    errors, lefts, rights = [], [], []
    for number, pair in enumerate(pairs, start=1):
        if not isinstance(pair, dict) or not _text(pair.get("left")) or not _text(pair.get("right")):
            errors.append(f"Пара {number}: потрібні непорожні рядки «left» і «right».")
            continue
        lefts.append(pair["left"]); rights.append(pair["right"])
    if len(set(lefts)) != len(lefts) or len(set(rights)) != len(rights):
        errors.append("Усі «left» і всі «right» мають бути різними, інакше пари вгадати неможливо.")
    return errors


def _scale_errors(data):
    errors = []
    if not _text(data.get("situation")):
        errors.append("«situation» має бути непорожнім рядком (опис ситуації).")
    labels = data.get("labels")
    if not _text_list(labels, 3):
        errors.append("«labels» має бути списком щонайменше з трьох підписів шкали.")
    correct = data.get("correct")
    if not isinstance(correct, list) or not correct or not all(_int(v) for v in correct):
        errors.append("«correct» має бути списком цілих чисел, наприклад [2, 3].")
    elif _text_list(labels, 3) and not all(1 <= v <= len(labels) for v in correct):
        errors.append(f"Числа в «correct» мають бути від 1 до {len(labels)}.")
    return errors


def validate_exercise_data(exercise_type, data):

    if not isinstance(data, dict):
        return ["Data має бути JSON-об'єктом у фігурних дужках { }."]
    if exercise_type == "face":
        return _choice_errors(data, needs_situation=False)
    if exercise_type == "situation":
        return _choice_errors(data, needs_situation=True)
    if exercise_type == "phrase":
        return _phrase_errors(data)
    if exercise_type == "match":
        return _match_errors(data)
    if exercise_type == "scale":
        return _scale_errors(data)
    if exercise_type == "novel":
        return [] if _text(data.get("build")) else ["«build» має бути шляхом до index.html новели."]
    return []
