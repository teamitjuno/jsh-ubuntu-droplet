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
from django.utils.translation import gettext_lazy as _

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


