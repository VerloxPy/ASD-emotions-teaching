from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

AVATAR_EMOJI = {"fox": "🦊", "cat": "🐱", "bear": "🐻"}


class User(AbstractUser):
    pass


class ChildProfile(models.Model):
    class Avatar(models.TextChoices):
        FOX = "fox", "Лисичка"
        CAT = "cat", "Котик"
        BEAR = "bear", "Ведмедик"

    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="children"
    )

    nickname = models.CharField(max_length=50)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    avatar = models.CharField(max_length=30, choices=Avatar.choices, default=Avatar.FOX)
    reduce_motion = models.BooleanField(default=True)
    sound_on = models.BooleanField(default=False)
    can_read = models.BooleanField("вміє читати", default=True)

    def __str__(self):
        return self.nickname

    @property
    def avatar_emoji(self):
        return AVATAR_EMOJI.get(self.avatar, "🙂")
