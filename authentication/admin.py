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
from django.shortcuts import redirect
import base64, binascii


class CustomUserChangeForm(forms.ModelForm):
    delete_avatar = forms.BooleanField(required=False)
    delete_user_certifikate = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("delete_avatar"):
            instance.avatar.delete(save=False)
        if self.cleaned_data.get("delete_user_certifikate"):
            instance.user_certifikate.delete(save=False)
        if commit:
            instance.save()
        return instance


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

def change_password(modeladmin, request, queryset):
    for user in queryset:
        return redirect(f"{user.id}/password")

update_users.short_description = "Update Users"


class ReadOnlyFieldsMixin:
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))  # type: ignore
        for field in self.opts.local_fields:  # type: ignore
            if hasattr(field, "editable") and not field.editable:
                readonly_fields.append(field.name)
        return readonly_fields


class CustomUserAdmin(ReadOnlyFieldsMixin, DefaultUserAdmin):
    form = CustomUserChangeForm
    actions = [update_users, change_password]
    search_fields = ["username", "first_name", "last_name", "email"]
    list_display = [
        "id",
        "username",
        "is_active",
        "role",
        "kuerzel",
        "typ",
        "zoho_id",
        "email",
        "phone",
        "salutation",
        "first_name",
        "last_name",
        "users_aufschlag",
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
                    "salutation",
                    "first_name",
                    "last_name",
                    "kuerzel",
                ),
            },
        ),
        (
            _("Persönliche Info"),
            {
                "fields": (
                    "avatar",
                    "delete_avatar",
                    "user_certifikate",
                    "delete_user_certifikate",
                    "role",
                    "beruf",
                    "typ",
                    "zoho_id",
                    "users_aufschlag",
                    "phone",
                    "records_fetch_limit",
                    "is_staff",
                    "is_active",
                    "zoho_data_text",
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
                    "initial_text_for_email",
                    "smtp_body",
                    "sonstiges",
                ),
            },
        ),
        (
            _("Initial data"),
            {
                "fields": (
                    "initial_verbrauch",
                    "initial_grundpreis",
                    "initial_arbeitspreis",
                    "initial_prognose",
                    "initial_zeitraum",
                    "initial_bis10kWp",
                    "initial_bis40kWp",
                    "initial_anz_speicher",
                    "initial_wandhalterung_fuer_speicher",
                    "initial_ausrichtung",
                    "initial_komplex",
                    "initial_solar_module",
                    "initial_modulanzahl",
                    "initial_garantieWR",
                    "initial_elwa",
                    "initial_thor",
                    "initial_heizstab",
                    "initial_anzOptimizer",
                    "initial_wallboxtyp",
                    "initial_wallbox_anzahl",
                    "initial_kabelanschluss",
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
                    "avatar",
                    "email",
                    "first_name",
                    "last_name",
                    "kuerzel",
                    "role",
                    "beruf",
                    "typ",
                    "zoho_id",
                    "users_aufschlag",
                    "is_staff",
                    "phone",
                    "sonstiges",
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

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("delete_avatar"):
            obj.avatar.delete(save=False)
        elif form.cleaned_data.get("delete_user_certifikate"):
            obj.user_certifikate.delete(save=False)

        super().save_model(request, obj, form, change)


@admin.register(User)
class UserAdmin(CustomUserAdmin):
    pass


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
