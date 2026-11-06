from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChildProfileForm, ComfortForm
from .utils import CHILD_SESSION_KEY, child_required


@login_required
def child_select(request):
    """Хто сьогодні навчається?"""
    children = request.user.children.order_by("id")
    if request.method == "POST":
        try:
            child_id = int(request.POST.get("child_id", ""))
        except ValueError:
            raise Http404
        child = get_object_or_404(children, id=child_id)
        request.session[CHILD_SESSION_KEY] = child.id
        return redirect("lessons:home")
    return render(request, "profiles/child_select.html", {"children": children})


@login_required
def child_add(request):
    form = ChildProfileForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        child = form.save(commit=False)
        child.parent = request.user
        child.save()
        request.session[CHILD_SESSION_KEY] = child.id
        messages.success(request, "Профіль створено.")
        return redirect("lessons:home")
    return render(request, "profiles/child_form.html", {"form": form})


@login_required
def child_edit(request, id):
    child = get_object_or_404(request.user.children, id=id)
    form = ChildProfileForm(request.POST or None, instance=child)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Зміни збережено.")
        return redirect("accounts:child_select")
    return render(request, "profiles/child_form.html", {"form": form})


@login_required
@child_required
def settings_page(request):
    """Налаштування сайту для обраної дитини."""
    form = ComfortForm(request.POST or None, instance=request.child)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Налаштування збережено.")
        return redirect("accounts:settings")
    return render(request, "profiles/settings.html", {"form": form, "child": request.child})
