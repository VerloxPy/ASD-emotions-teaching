from django.db import models


class Attempt(models.Model):
    child = models.ForeignKey("accounts.ChildProfile", on_delete=models.CASCADE)
    exercise = models.ForeignKey("lessons.Exercise", on_delete=models.CASCADE)
    answer = models.JSONField()
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.child} → {self.exercise_id}: {'✓' if self.is_correct else '✗'}"