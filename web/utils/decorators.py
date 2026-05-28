from django.contrib.auth.decorators import login_required, user_passes_test


def is_staff(user):
    return user.is_staff


def require_staff(view_func):
    return user_passes_test(is_staff)(login_required(view_func))
