from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models

EMOTION_PALETTE = ["#F2C14E", "#6FA8DC", "#E58F76", "#A596CF", "#68BBA9", "#E5A0BC"]


class Emotion(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=50)
    color = models.CharField(
        "колір", max_length=7, blank=True,
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Формат кольору: #RRGGBB")],
        help_text="Необов'язково, наприклад #F2C14E. Якщо порожньо, колір обереться автоматично.",
    )

    def __str__(self):
        return self.name

    @property
    def display_color(self):
        return self.color or EMOTION_PALETTE[(self.pk or 0) % len(EMOTION_PALETTE)]


class Level(models.Model):
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Exercise(models.Model):
    class Type(models.TextChoices):
        FACE_TO_EMOTION = "face", "Яка це емоція?"
        SITUATION = "situation", "Що відчуває людина?"
        PHRASE = "phrase", "Як би ти це сказав?"
        MATCH = "match", "Знайди пару"
        SCALE = "scale", "Шкала сили емоції"
        NOVEL = "novel", "Новела"
        READ_ALOUD = "read_aloud", "Виразне читання"

    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="exercises")
    emotion = models.ForeignKey(Emotion, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices)
    order = models.PositiveIntegerField()
    prompt = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    image = models.ImageField(upload_to="exercises/", blank=True)
    audio = models.FileField(upload_to="exercises/audio/", blank=True)

    class Meta:
        ordering = ["level", "order"]

    def __str__(self):
        return f"{self.level} / {self.order}: {self.prompt[:40]}"


class ReadingLine(models.Model):
    """Одне речення вправи «Виразне читання»: диктор читає, дитина повторює."""

    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, related_name="lines",
        limit_choices_to={"type": "read_aloud"}, verbose_name="вправа",
    )
    order = models.PositiveIntegerField("порядок")
    text = models.TextField("текст речення")
    audio = models.FileField(
        "озвучення диктора", upload_to="reading/audio/", blank=True,
        validators=[FileExtensionValidator(["mp3", "ogg", "wav", "m4a"])],
        help_text="Файл mp3, ogg, wav або m4a. Без нього речення показується без звуку.",
    )
    emotion = models.ForeignKey(
        Emotion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="емоція",
    )
    delivery = models.CharField(
        "підказка про інтонацію", max_length=120, blank=True,
        help_text="Наприклад: «говоримо радісно й голосно».",
    )
    image = models.ImageField("картинка", upload_to="reading/images/", blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "речення для читання"
        verbose_name_plural = "речення для читання"

    def __str__(self):
        return self.text[:40]
