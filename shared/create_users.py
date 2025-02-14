from authentication.models import User
from django.contrib.auth import get_user_model
from get_vertriebler_list import fetch_vertriebler_list_IDs
from config.settings import (
    DEFAULT_PHONE,
    DEFAULT_USER_CREATION_PASSWORD,
    DEFAULT_EMAIL_DOMAIN,
)

zoho_users_list = fetch_vertriebler_list_IDs()


def create_users(zoho_users_list):
    # This is not the command called from the admin panel, see authentication/management/commands/update_vertrieblers.py
    phone_counter = 4
    for user_info in zoho_users_list:
        first_name, last_name = user_info[0].split(" ")
        zoho_id = int(user_info[1])
        username = (first_name + last_name).lower()
        email = first_name[0].lower() + last_name.lower() + f"{DEFAULT_EMAIL_DOMAIN}"
        kuerzel = first_name[0].upper() + last_name[0].upper()
        phone = f"+{DEFAULT_PHONE}" + str(phone_counter)

        # Check if a User with the provided zoho_id exists
        user_exists = User.objects.filter(zoho_id=zoho_id).exists()

        # If the User does not exist, create a new User
        if not user_exists:
            new_user = User.objects.create(
                zoho_id=zoho_id,
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                is_staff=False,
                beruf="Vertrieb",
                users_aufschlag=0,
                typ="Vertrieb",
                kuerzel=kuerzel,
                is_active=True,
                is_superuser=False,
            )
            new_user.set_password(f"{DEFAULT_USER_CREATION_PASSWORD}")
            new_user.save()
            phone_counter += 1
