from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group

from .models import TblUser


class TblUsersBackend:
    """Authenticate against tbl_users and map role to Django groups."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        tbl_user = TblUser.objects.filter(username=username, is_active=True).first()
        if not tbl_user:
            return None

        if not self._password_matches(password, tbl_user.password_hash):
            return None

        User = get_user_model()
        django_user, _ = User.objects.get_or_create(
            username=tbl_user.username,
            defaults={
                "is_active": bool(tbl_user.is_active),
            },
        )

        django_user.is_active = bool(tbl_user.is_active)
        django_user.save(update_fields=["is_active"])

        group, _ = Group.objects.get_or_create(name=tbl_user.role)
        django_user.groups.clear()
        django_user.groups.add(group)

        return django_user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def _password_matches(raw_password, stored_password):
        if not stored_password:
            return False

        if stored_password.startswith(("pbkdf2_", "argon2$", "bcrypt$")):
            return check_password(raw_password, stored_password)

        return raw_password == stored_password
