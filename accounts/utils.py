from functools import wraps

from django.shortcuts import redirect

CHILD_SESSION_KEY = "active_child_id"


def get_active_child(request):

    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None

    children = list(user.children.order_by("id"))
    if not children:
        return None

    chosen_id = request.session.get(CHILD_SESSION_KEY)
    for child in children:
        if child.id == chosen_id:
            return child

    if len(children) == 1:  # єдина дитина обирається сама
        request.session[CHILD_SESSION_KEY] = children[0].id
        return children[0]
    return None


def child_required(view):

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        child = get_active_child(request)
        if child is None:
            if request.user.children.exists():
                return redirect("accounts:child_select")
            return redirect("accounts:child_add")
        request.child = child
        return view(request, *args, **kwargs)
    return wrapper
