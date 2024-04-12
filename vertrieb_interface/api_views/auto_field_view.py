# Python standard libraries
import json

# Django related imports
from django.views.generic import View
from django.http import (
    JsonResponse,
)

from vertrieb_interface.api_views.auth_checkers import VertriebCheckMixin
from authentication.models import User


class VertriebAutoFieldView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        # Load data from user's stored JSON text, default to empty list if not available
        try:
            self.data = json.loads(user.zoho_data_text) if user.zoho_data_text else []
        except json.JSONDecodeError:
            self.data = []  # Handle possible JSON decoding errors

        name = request.GET.get("name", None)
        if name:  # Check if name parameter is provided and not None
            data = next((item for item in self.data if item["name"] == name), None)
            if data is None:
                return JsonResponse({"error": "No data found for the specified name"}, status=404)
            return JsonResponse(data, safe=False)  # Return the found data
        else:
            return JsonResponse({"error": "No name parameter provided"}, status=400)  # No name provided in GET request
