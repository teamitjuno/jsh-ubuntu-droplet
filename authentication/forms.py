from django import forms
from django.contrib.auth.models import Group
from .models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django import forms
from .models import User
import base64

from django import forms
from .models import User


from django import forms
from django.contrib.auth.forms import SetPasswordForm

from django import forms
from .models import Role


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            "name",
        ]


class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar"]


class TopVerkauferContainerViewForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "top_verkaufer_container_view",
            "profile_container_view",
            "activity_container_view",
            "angebot_statusubersicht_view",
            "pv_rechner_view",
            "anzahl_sol_module_view",
        ]


class AdminPasswordChangeForm(SetPasswordForm):
    """
    A form that lets a user change set their password without entering the old
    password
    """

    def __init__(self, user, *args, **kwargs):
        super(AdminPasswordChangeForm, self).__init__(user, *args, **kwargs)

    def clean_old_password(self):
        # This method is not really required here since we've removed the need for the old password.
        return self.user.password


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"  # Including all fields for the example

    email = forms.EmailField(
        label="E-Mail",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email Address",
                "id": "email",
            }
        ),
    )

    username = forms.CharField(
        label="Username",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "id": "username",
            }
        ),
    )

    first_name = forms.CharField(
        label="First Name",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name",
                "id": "first_name",
            }
        ),
    )

    last_name = forms.CharField(
        label="Last Name",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name",
                "id": "last_name",
            }
        ),
    )

    phone = forms.CharField(
        label="Phone",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone",
                "id": "phone",
            }
        ),
    )

    beruf = forms.ChoiceField(
        label="Beruf",
        choices=User.beruf.field.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_beruf",
            }
        ),
        required=False,
    )
    is_staff = forms.BooleanField(
        label="Is Admin",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_is_staff",
            }
        ),
    )
    users_aufschlag = forms.IntegerField(
        initial=0,
        label="Vertrieb Aufschlag",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_users_aufschlag",
            }
        ),
    )

    typ = forms.ChoiceField(
        label="Typ",
        choices=User.typ.field.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_typ",
            }
        ),
        required=False,
    )

    google_account = forms.EmailField(
        label="Google Account",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Google Email Address",
                "id": "google_account",
            }
        ),
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),  # Add a CSS class to the select widget
        label="User's Role",  # Custom label for the role field
    )

    age = forms.IntegerField(
        label="Age",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Age",
                "id": "age",
            }
        ),
    )

    avatar = forms.ImageField(
        label="Profile Picture",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control-file",
                "id": "avatar",
            }
        ),
    )

    kuerzel = forms.CharField(
        label="Kuerzel",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kuerzel",
                "id": "kuerzel",
            }
        ),
    )

    gerat = forms.CharField(
        label="Gerät",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Gerät",
                "id": "gerat",
            }
        ),
    )

    imei = forms.CharField(
        label="IMEI",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "IMEI",
                "id": "imei",
            }
        ),
    )

    anbieter = forms.CharField(
        label="Anbieter",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Anbieter",
                "id": "anbieter",
            }
        ),
    )

    google_passwort = forms.CharField(
        label="Google Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Google Password",
                "id": "google_passwort",
            }
        ),
    )

    sim_pin = forms.CharField(
        label="SIM PIN",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "SIM PIN",
                "id": "sim_pin",
            }
        ),
    )

    zoho_data_text = forms.CharField(
        label="Zoho Data Text",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Zoho Data Text",
                "id": "zoho_data_text",
                "rows": 3,
            }
        ),
    )

    sonstiges = forms.CharField(
        label="Sonstiges",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Sonstiges",
                "id": "sonstiges",
                "rows": 3,
            }
        ),
    )

    smtp_server = forms.CharField(
        label="SMTP Server",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "SMTP Server",
                "id": "smtp_server",
            }
        ),
    )

    smtp_port = forms.CharField(
        label="SMTP Port",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "SMTP Port",
                "id": "smtp_port",
            }
        ),
    )

    smtp_username = forms.CharField(
        label="SMTP Username",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "SMTP Username",
                "id": "smtp_username",
            }
        ),
    )

    smtp_password = forms.CharField(
        label="SMTP Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "SMTP Password",
                "id": "smtp_password",
            }
        ),
    )

    smtp_subject = forms.CharField(
        label="SMTP Subject",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "SMTP Subject",
                "id": "smtp_subject",
                "rows": 2,
            }
        ),
    )

    smtp_body = forms.CharField(
        label="SMTP Body",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "SMTP Body",
                "id": "smtp_body",
                "rows": 4,
            }
        ),
    )

    def __init__(self, *args, user, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            if self.initial.get(field):
                self.fields[field].widget.attrs.update(
                    {"placeholder": self.initial[field]}
                )
