from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dotenv import set_key
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

User = get_user_model()


class Command(BaseCommand):
    help = "Updates the User model with the list of users from Zoho"

    def fetch_vertriebler_list_IDs(self):
        access_token = ZOHO_ACCESS_TOKEN
        if not access_token:
            access_token = self.refresh_access_token()

        url = BASE_URL + "/Au_endienstler_API"

        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
        }

        # Define an empty set to store unique Vertriebler data
        vertriebler_set = set()

        # Specify the number of records to fetch per request
        limit = 100
        start_index = 0

        while True:
            params = {
                "from": start_index,
                "limit": limit,
                "criteria": "Mail != null"
            }
            response = requests.get(url, headers=headers, params=params)  # type: ignore
            if response.status_code == 401:
                access_token = self.refresh_access_token()
                headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
                continue

            # Check the response status code
            elif response.status_code != 200:
                print(f"Failed to fetch data, status code: {response.status_code}")
                break
            print(f"access_token is alive, status code: {response.status_code}")
            data = json.loads(response.text)

            if not data["data"]:
                break

            for record in data["data"]:
                if (
                    "Name" in record
                    and "Mail" in record
                    and "ID" in record
                    and "Mobil" in record
                    and "Anrede" in record
                    and "Stellenbezeichnung" in record
                ):
                    is_active = record["Unternehmen_verlassen_am"] == ""
                    print(f"{is_active}: {record}")
                    vertriebler_set.add(
                        (
                            record["Name"],
                            record["ID"],
                            record["Mail"],
                            record["Mobil"],
                            record["Anrede"],
                            record["Stellenbezeichnung"],
                            is_active,
                        )
                    )

            # Update the start index for the next batch of records
            start_index += limit

        # Convert the set to a list and print
        vertriebler_list = list(vertriebler_set)
        vertriebler_list = json.dumps(vertriebler_list, indent=4)
        return vertriebler_list

    def refresh_access_token(self):
        client_id = ZOHO_CLIENT_ID
        client_secret = ZOHO_CLIENT_SECRET
        refresh_token = ZOHO_REFRESH_TOKEN

        url = f"https://accounts.zoho.eu/oauth/v2/token?refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token"

        response = requests.post(url)

        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            print("Access token refreshed.", new_access_token)

            set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_access_token)

            return new_access_token
        else:
            print(f"Error refreshing token: {response.status_code}")

    def handle(self, *args, **kwargs):
        zoho_users_list = self.fetch_vertriebler_list_IDs()
        # Parse JSON string back to Python list
        zoho_users_list = json.loads(zoho_users_list)

        phone_counter = 4
        for user_info in zoho_users_list:
            # Ensure that user_info is a list with at least two elements
            if isinstance(user_info, list) and len(user_info) >= 2:
                print(user_info)
                names = user_info[0].split(" ")
                if len(names) < 2:
                    self.stdout.write(
                        f"Skipping user {user_info[0]} due to improper name format."
                    )
                    continue
                first_name = names[0]
                last_name = " ".join(names[1:]) if len(names) > 1 else ""
                zoho_id = int(user_info[1])
                username = (first_name + last_name).lower()
                email = user_info[2]
                if email == None or email == "":
                    continue
                kuerzel = email[0:email.index("@")].upper()
                if len(kuerzel) > 3:
                    kuerzel = kuerzel[:3]
                phone = user_info[3]
                if phone == "":
                    phone = None
                typ = "Vertrieb"
                if user_info[5] == "Handelsvertreter/in":
                    typ = "Handelsvertretung"
                elif user_info[5] == "Regionalleitung":
                    typ = "Regionalleitung"

                    # Check if a User with the provided zoho_id exists
                user_exists = User.objects.filter(zoho_id=zoho_id).exists()

                # If the User does not exist, create a new User
                if not user_exists and user_info[6]:
                    new_user = User.objects.create(
                        zoho_id=zoho_id,
                        email=email,
                        username=username,
                        salutation=user_info[4],
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        is_staff=False,
                        beruf="Vertrieb",
                        users_aufschlag=0,
                        typ=typ,
                        kuerzel=kuerzel,
                        is_active=True,
                        is_superuser=False,
                    )
                    new_user.set_password(f"{DEFAULT_USER_CREATION_PASSWORD}")
                    new_user.save()
                    phone_counter += 1
                else:
                    User.objects.filter(zoho_id=zoho_id).update(email=email)
                    User.objects.filter(zoho_id=zoho_id).update(username=username)
                    User.objects.filter(zoho_id=zoho_id).update(salutation=user_info[4])
                    User.objects.filter(zoho_id=zoho_id).update(phone=phone)
                    User.objects.filter(zoho_id=zoho_id).update(first_name=first_name)
                    User.objects.filter(zoho_id=zoho_id).update(last_name=last_name)
                    User.objects.filter(zoho_id=zoho_id).update(typ=typ)
                    User.objects.filter(zoho_id=zoho_id).update(kuerzel=kuerzel)
                    User.objects.filter(zoho_id=zoho_id).update(is_active=user_info[6])
            else:
                self.stdout.write(
                    f"Skipping user {user_info} due to incorrect data format."
                )
