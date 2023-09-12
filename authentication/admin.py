from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy as _
from django.core.management import call_command
from .models import Role, User
from django.contrib import admin
from django.forms import FileInput
from django.db import models
from django import forms
from django.core.exceptions import ValidationError
import base64, binascii


class Base64Field(forms.Field):
    def clean(self, value):
        value = super().clean(value)
        try:
            base64.b64decode(value, validate=True)
            return value
        except binascii.Error:
            raise ValidationError("Invalid base64 string")


def update_users(modeladmin, request, queryset):
    call_command("update_users")


update_users.short_description = "Update Users"


class ReadOnlyFieldsMixin:
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))  # type: ignore
        for field in self.opts.local_fields:  # type: ignore
            if hasattr(field, "editable") and not field.editable:
                readonly_fields.append(field.name)
        return readonly_fields


class CustomUserAdmin(ReadOnlyFieldsMixin, DefaultUserAdmin):
    actions = [update_users]
    search_fields = ["username", "first_name", "last_name", "email"]
    list_display = [
        "id",
        "username",
        "zoho_id",
        "email",
        "first_name",
        "last_name",
        "beruf",
        "is_staff",
        "users_aufschlag",
        "typ",
        "kuerzel",
        "gerat",
        "imei",
        "anbieter",
        "google_account",
        "google_passwort",
        "sim_pin",
        "sonstiges",
        "phone",
        "age",
        "role",
        "last_login",
    ]
    list_filter = ["beruf", "typ", "role", "created_at"]
    ordering = ("email",)
    fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password",
                    "email",
                    "first_name",
                    "last_name",
                ),
            },
        ),
        (
            _("Persönliche Info"),
            {
                "fields": (
                    "avatar",
                    "beruf",
                    "is_staff",
                    "users_aufschlag",
                    "typ",
                    "kuerzel",
                    "phone",
                    "age",
                    "role",
                ),
            },
        ),
        (
            _("Handy und Gerät data"),
            {
                "fields": (
                    "gerat",
                    "imei",
                    "anbieter",
                    "google_account",
                    "google_passwort",
                    "sim_pin",
                    "sonstiges",
                ),
            },
        ),
        (
            _("SMTP and Email data"),
            {
                "fields": (
                    "smtp_server",
                    "smtp_port",
                    "smtp_username",
                    "smtp_password",
                    "smtp_subject",
                    "smtp_body",
                    "zoho_data_text",
                ),
            },
        ),
        (_("Permissions"), {"fields": ("user_permissions",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "email",
                    "first_name",
                    "last_name",
                    "avatar",
                    "beruf",
                    "users_aufschlag",
                    "typ",
                    "kuerzel",
                    "gerat",
                    "imei",
                    "anbieter",
                    "google_account",
                    "google_passwort",
                    "sim_pin",
                    "sonstiges",
                    "phone",
                    "age",
                    "role",
                    "smtp_server",
                    "smtp_port",
                    "smtp_username",
                    "smtp_password",
                    "smtp_subject",
                    "smtp_body",
                ),
            },
        ),
    )
    filter_horizontal = ("user_permissions",)
    formfield_overrides = {
        models.ImageField: {"widget": FileInput},
    }


@admin.register(User)
class UserAdmin(CustomUserAdmin):
    pass


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
