from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dotenv import set_key
from authentication.models import Role
import requests
import json
from random import randint
from config.settings import (
    ENV_FILE,
    ZOHO_ACCESS_TOKEN,
    BASE_URL,
    BASE_URL_PRIV_KUNDEN,
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    DEFAULT_EMAIL_DOMAIN,
    DEFAULT_PHONE,
    DEFAULT_USER_CREATION_PASSWORD,
)
from vertrieb_interface.tasks import (
    delete_unassigned_vertriebangebot_day_old,
    delete_unassigned_vertriebticket_day_old,
    delete_angenommen_vertriebangebot_two_months_old,
    delete_vertriebangebot_six_weeks_old,
)

User = get_user_model()

class Command(BaseCommand):
    help = "Deletes unused data like old VertriebAngebots und VertriebTickets"

    def handle(self, *args, **kwargs):
        result = delete_unassigned_vertriebangebot_day_old()
        result = delete_unassigned_vertriebticket_day_old()
        result = delete_angenommen_vertriebangebot_two_months_old()

