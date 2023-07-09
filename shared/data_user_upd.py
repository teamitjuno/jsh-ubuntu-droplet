import os
import json
from django.db import transaction
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "config.settings"
)  # Replace 'your_project' with your actual project name

import django

django.setup()

from authentication.models import (
    User,
)  # Replace `authentication` with your actual Django app name

# Load JSON data
with open("Ger.json", "r") as f:
    data = json.load(f)

# Create a mapping of JSON keys to User model fields
json_to_model_fields = {
    "K\u00fcrzel": "kuerzel",
    "Ger\u00e4t": "gerat",
    "IMei": "imei",
    "Handynummer": "phone",
    "Anbieter": "anbieter",
    "Mail ": "google_account",
    "Passwort ": "google_passwort",
    "Sim Pin ": "sim_pin",
}

# Start a transaction
with transaction.atomic():
    for item in data:
        # Find user by `kuerzel`
        try:
            user = User.objects.get(kuerzel=item.get("K\u00fcrzel"))
        except User.DoesNotExist:
            continue  # Skip if user does not exist

        # Update fields
        for json_field, model_field in json_to_model_fields.items():
            if item.get(json_field):  # If field in JSON is not empty
                setattr(user, model_field, item.get(json_field))

        # Save changes
        user.save()
