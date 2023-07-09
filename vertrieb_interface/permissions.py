from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import resolve_url
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy


def role_required(
    allowed_roles, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME
):
    """
    Decorator for views that checks that the user is logged in and has one of the specified roles,
    redirecting to the log-in page if necessary.
    """

    def check_role(user):
        if user.is_authenticated and user.role is not None:
            return user.role.name in allowed_roles
        return False

    return user_passes_test(
        check_role, login_url=login_url, redirect_field_name=redirect_field_name
    )


def admin_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the logged in user is an admin,
    redirects to the log-in page if necessary.
    """
    actual_decorator = role_required(
        allowed_roles=["admin"],
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def user_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the logged in user is a user,
    redirects to the log-in page if necessary.
    """
    actual_decorator = role_required(
        allowed_roles=["user"],
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


class RoleRequired(UserPassesTestMixin):
    """Mixin used for views that checks that the user is logged in and has the specified role."""

    login_url = reverse_lazy("login")  # replace 'login' with your login view name
    allowed_roles = []

    def test_func(self):
        if self.request.user.is_authenticated and self.request.user.role is not None: #type:ignore
            return self.request.user.role.name in self.allowed_roles #type:ignore
        return False


class AdminRequiredMixin(RoleRequired):
    """Mixin used for views that checks that the user is logged in and is an admin."""

    allowed_roles = ["admin"]


class UserRequiredMixin(RoleRequired):
    """Mixin used for views that checks that the user is logged in and is a user."""

    allowed_roles = ["user"]
