from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Emotion, Exercise, Level, ReadingLine

DATA_HELP = """
<details><summary>Приклади формату Data для кожного типу</summary>
<pre style="white-space: pre-wrap">
Яка це емоція?:
{"options": ["страх", "радість", "злість"], "correct": "страх", "explanation": "..."}

Що відчуває людина?:
{"situation": "...", "options": ["страх", "радість"], "correct": "страх", "explanation": "..."}

Як би ти це сказав?:
{"situation": "...", "options": [{"text": "...", "fits": true, "feedback": "..."}, {"text": "...", "fits": false, "feedback": "..."}]}

Знайди пару:
{"pairs": [{"left": "Страх", "right": "..."}, {"left": "Сором", "right": "..."}], "explanation": "..."}

Шкала сили емоції:
{"situation": "...", "labels": ["зовсім ні", "трохи", "помірно", "сильно", "дуже сильно"], "correct": [4, 5], "explanation": "..."}

Новела:
{"build": "novels/radist/index.html"}

Виразне читання: Data можна лишити порожнім, речення додаються нижче.
</pre></details>
"""


class ReadingLineInline(admin.StackedInline):
    """Речення для вправи типу «Виразне читання» (для інших типів не потрібні)."""
    model = ReadingLine
    extra = 1
    fields = ("order", "text", "audio", "emotion", "delivery", "image")


admin.site.register(Emotion)
admin.site.register(Level)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    inlines = [ReadingLineInline]
    list_display = ("__str__", "type", "emotion")
    list_filter = ("type", "level")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "data":
            field.help_text = mark_safe(DATA_HELP)
        return field
