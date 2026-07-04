from django.contrib.auth.decorators import user_passes_test


def role_required(*allowed_roles):
    """Allow access only to users whose role matches allowed_roles."""

    def predicate(user):
        if not user.is_authenticated:
            return False

        if user.is_superuser and "Admin" in allowed_roles:
            return True

        return user.groups.filter(name__in=allowed_roles).exists()

    return user_passes_test(predicate, login_url="login")
