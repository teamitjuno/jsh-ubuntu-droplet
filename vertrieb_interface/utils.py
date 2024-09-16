import hashlib
from django.core.exceptions import ValidationError
from authentication.models import User

def validate_range(value):
    if not isinstance(value, int):
        if value < 0 or value > 6:
            raise ValidationError(
                ("Ungültige Eingabe: %(value)s. Der gültige Bereich ist 0-6."),
                params={"value": value},
            )


def extract_modulleistungWp(model_name):
    parts = model_name.split()
    for part in parts:
        if part.isdigit():
            return int(part)
    return None


def sanitize_cache_key(key):
    sanitized_key = hashlib.md5(key.encode()).hexdigest()
    return sanitized_key


def changeVerguetung():
    users = User.objects.all()
    for user in users:
        User.objects.filter(zoho_id=user.zoho_id).update(initial_bis10kWp=8.03)
        User.objects.filter(zoho_id=user.zoho_id).update(initial_bis40kWp=6.95)