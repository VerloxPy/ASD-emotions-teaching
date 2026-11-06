from django import forms
from django.utils import timezone

from .models import AVATAR_EMOJI, ChildProfile


class ChildProfileForm(forms.ModelForm):
    """Ім'я, аватар і рік народження. Комфорт налаштовується на окремій сторінці."""

    class Meta:
        model = ChildProfile
        fields = ["nickname", "birth_year", "avatar", "can_read"]
        labels = {
            "nickname": "Ім'я або прізвисько",
            "birth_year": "Рік народження (необов'язково)",
            "can_read": "Дитина вміє читати",
        }
        help_texts = {
            "nickname": "Справжнє ім'я не потрібне: підійде будь-яке ім'я чи прізвисько.",
            "birth_year": "Допомагає підбирати вправи. Можна залишити порожнім.",
            "can_read": "Якщо ні, у вправах на виразне читання текст не показується: дитина слухає й повторює. Змінити можна пізніше в налаштуваннях.",
        }
        widgets = {"avatar": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.avatar_options = [
            {"value": value, "label": label, "emoji": AVATAR_EMOJI.get(value, "🙂")}
            for value, label in ChildProfile.Avatar.choices
        ]

    def clean_nickname(self):
        return self.cleaned_data["nickname"].strip()

    def clean_birth_year(self):
        year = self.cleaned_data.get("birth_year")
        if year is not None:
            this_year = timezone.now().year
            if not (this_year - 25 <= year <= this_year):
                raise forms.ValidationError("Перевірте рік народження.")
        return year


class ComfortForm(forms.ModelForm):
    """Налаштування для обраної дитини: комфорт і читання."""

    class Meta:
        model = ChildProfile
        fields = ["reduce_motion", "sound_on", "can_read"]
        labels = {
            "reduce_motion": "Менше анімації",
            "sound_on": "Увімкнути звук",
            "can_read": "Дитина вміє читати",
        }
        help_texts = {
            "reduce_motion": "Прибирає плавні переходи й рух на сторінках.",
            "sound_on": "Для майбутніх звукових ефектів. Озвучення у вправі на читання вмикається кнопкою «Послухати» і від цього налаштування не залежить.",
            "can_read": "Якщо вимкнено, у вправах на виразне читання текст не показується: дитина слухає й повторює. Дорослий бачить текст у розділі «Для дорослого».",
        }
