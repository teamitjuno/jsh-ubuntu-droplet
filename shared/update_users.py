from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from authentication.models import User
import requests
import json
from config.settings import BASE_URL_PRIV_KUNDEN


class Command(BaseCommand):
    help = "Fetches Vertriebler data from Zoho and updates Django User model"

    def handle(self, *args, **options):
        url = BASE_URL_PRIV_KUNDEN
        headers = {"Authorization": "Zoho-oauthtoken your_auth_token"}
        vertriebler_set = set()
        limit = 200
        start_index = 0

        while True:
            params = {"from": start_index, "limit": limit}
            response = requests.get(url, headers=headers, params=params)  # type: ignore

            if response.status_code != 200:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to fetch data, status code: {response.status_code}"
                    )
                )
                break

            data = json.loads(response.text)

            if not data["data"]:
                break

            for record in data["data"]:
                if (
                    "Vertriebler" in record
                    and "display_value" in record["Vertriebler"]
                    and "ID" in record["Vertriebler"]
                ):
                    vertriebler_set.add(
                        (
                            record["Vertriebler"]["display_value"],
                            record["Vertriebler"]["ID"],
                        )
                    )

            start_index += limit

        for name, zoho_id in vertriebler_set:
            try:
                user, created = User.objects.get_or_create(name=name, zoho_id=zoho_id)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully created User: {user.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"User already exists: {user.name}")
                    )

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Failed to create User: {str(e)}"))
                pass
