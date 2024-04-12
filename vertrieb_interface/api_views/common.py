# common.py
import json
from django.http import HttpResponse


def load_json_data(text):
    try:
        return json.loads(text) if text else []
    except json.JSONDecodeError:
        return None
