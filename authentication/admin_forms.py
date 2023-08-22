from django import forms
from django.contrib.auth.models import Group
from .models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin


class UserAdminCreationForm(forms.ModelForm):
    gerat = forms.CharField(required=False)
    is_staff = forms.BooleanField(required=False)
    imei = forms.IntegerField(required=False)
    anbieter = forms.CharField(required=False)
    google_account = forms.EmailField(required=False)
    google_passwort = forms.CharField(required=False)
    sim_pin = forms.IntegerField(required=False)
    is_superuser = forms.BooleanField(required=False)
    zoho_data = forms.JSONField(required=False)
    sonstiges = forms.CharField(widget=forms.Textarea, required=False)

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = "__all__"

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

            if user.beruf == "Electrician":
                user.groups.add(Group.objects.get(name="Elektriker"))
            elif user.beruf == "Verkäufer":
                user.groups.add(Group.objects.get(name="Verkäufer"))

            user.save()

        return user


class MyUserAdmin(DefaultUserAdmin):
    form = UserAdminCreationForm


admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
