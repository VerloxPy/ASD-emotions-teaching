from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("children/", views.child_select, name="child_select"),
    path("children/add/", views.child_add, name="child_add"),
    path("children/<int:id>/edit/", views.child_edit, name="child_edit"),
    path("settings/", views.settings_page, name="settings"),
]
