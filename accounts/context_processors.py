from django.conf import settings

from .utils import get_active_child


def site(request):
    """Спільні змінні для всіх шаблонів."""
    child = get_active_child(request)
    return {
        "active_child": child,
        "reduce_motion": bool(child and child.reduce_motion),
        "google_enabled": settings.GOOGLE_LOGIN_ENABLED,
        "debug": settings.DEBUG,
    }
