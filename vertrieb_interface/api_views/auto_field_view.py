# Python standard libraries
import json

# Django related imports
from django.views.generic import View
from django.http import (
    JsonResponse,
)

from vertrieb_interface.api_views.auth_checkers import VertriebCheckMixin
from authentication.models import User


class VertriebAutoFieldView(View, VertriebCheckMixin):
    data = []

    def get(self, request, *args, **kwargs):
        profile, created = User.objects.get_or_create(zoho_id=request.user.zoho_id)
        self.data = json.loads(profile.zoho_data_text)
        try:
            self.data != []
            name = request.GET.get("name", None)
            data = next((item for item in self.data if item["name"] == name), None)

            return JsonResponse(data)
        except:
            name = request.GET.get("name", None)
            data = next((item for item in self.data if item["name"] == name), None)

            if data is None:
                data = {}
            return JsonResponse(data)
