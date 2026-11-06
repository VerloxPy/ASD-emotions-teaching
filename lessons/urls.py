from django.urls import path

from . import views

app_name = "lessons"

urlpatterns = [
    path("", views.home, name="home"),
    path("exercises/", views.level_list, name="level_list"),
    path("stats/", views.stats, name="stats"),
    path("session/start/", views.session_start, name="session_start"),
    path("session/resume/", views.session_resume, name="session_resume"),
    path("session/done/", views.session_done, name="session_done"),
    path("exercise/<int:id>/", views.exercise_detail, name="exercise_detail"),
    path("exercise/<int:id>/answer/", views.exercise_answer, name="exercise_answer"),
    path("exercise/<int:id>/novel-result/", views.novel_result, name="novel_result"),
    path("exercise/<int:id>/reading-result/", views.reading_result, name="reading_result"),
]
