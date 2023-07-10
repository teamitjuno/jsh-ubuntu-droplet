import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from authentication.models import User


class Command(BaseCommand):
    help = 'Update User models from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The path to the JSON file')

    def handle(self, *args, **options):
        json_file = options['json_file']

        if not os.path.exists(json_file):
            raise CommandError('JSON file "%s" does not exist' % json_file)

        with open(json_file, 'r') as f:
            data = json.load(f)

        json_to_model_fields = {
            "K\u00fcrzel": "kuerzel",
            "Ger\u00e4t": "gerat",
            "IMei": "imei",
            "Handynummer": "phone",
            "Anbieter": "anbieter",
            "Mail ": "google_account",
            "Passwort ": "google_passwort",
            "Sim Pin ": "sim_pin",
            "SMTP_PASS" : "smtp_password",
            "SMTP_USER" : "smtp_username"
        }

        with transaction.atomic():
            for item in data:
                try:
                    user = User.objects.get(kuerzel=item.get("K\u00fcrzel"))
                except User.DoesNotExist:
                    continue

                for json_field, model_field in json_to_model_fields.items():
                    if item.get(json_field):
                        setattr(user, model_field, item.get(json_field))

                user.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated User data.'))
