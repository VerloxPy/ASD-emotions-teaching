from django.contrib import admin

from .models import Emotion, Exercise, Level, ReadingLine

admin.site.register(Emotion)
admin.site.register(Level)


class ReadingLineInline(admin.StackedInline):
    """Речення для вправи типу «Виразне читання» (для інших типів не потрібні)."""
    model = ReadingLine
    extra = 1
    fields = ("order", "text", "audio", "emotion", "delivery", "image")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    inlines = [ReadingLineInline]
    list_display = ("__str__", "type", "emotion")
    list_filter = ("type", "level")
