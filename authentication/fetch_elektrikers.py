import json, requests, time
from dotenv import set_key, load_dotenv
from random import randint
from django.contrib.auth import get_user_model
from config.settings import (
    ENV_FILE,
    BASE_URL,
    ACCESS_TOKEN_URL,
    ZOHO_ACCESS_TOKEN,
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    DEFAULT_EMAIL_DOMAIN,
    DEFAULT_USER_CREATION_PASSWORD,
)

# Constants
load_dotenv(ENV_FILE)

User = get_user_model()

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
LIMIT = 100
MAX_RETRIES = 5
SLEEP_TIME = 1


class APIException(Exception):
    pass


class UnauthorizedException(APIException):
    pass


class RateLimitExceededException(APIException):
    pass


def get_headers():
    access_token = ZOHO_ACCESS_TOKEN
    print(access_token)
    return {"Authorization": f"Zoho-oauthtoken {access_token}"}


def refresh_access_token():
    client_id = ZOHO_CLIENT_ID
    client_secret = ZOHO_CLIENT_SECRET
    refresh_token = ZOHO_REFRESH_TOKEN

    url = f"{ACCESS_TOKEN_URL}?refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token"
    response = requests.post(url)
    if response.status_code != HTTP_OK:
        raise APIException(f"Error refreshing token: {response.status_code}")

    data = response.json()
    new_access_token = data.get("access_token")
    set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_access_token)
    return new_access_token


def fetch_records(
    endpoint, headers, params, retries=MAX_RETRIES, sleep_time=SLEEP_TIME
):
    for i in range(retries):
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            if response.status_code == HTTP_UNAUTHORIZED:
                headers["Authorization"] = f"Zoho-oauthtoken {refresh_access_token()}"
                continue
            elif response.status_code == 429:
                time.sleep(sleep_time)
                sleep_time *= 2
                continue
            elif response.status_code != HTTP_OK:
                raise APIException(f"HTTPError: {response.status_code}")

            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"An error occurred: {err}")
            continue
    raise APIException("Max retries exceeded.")


def create_user(user_info):
    if isinstance(user_info, list) and len(user_info) >= 2:
        names = user_info[0].split(" ")
        if len(names) < 2:
            print(f"Skipping user {user_info[0]} due to improper name format.")
            return

        first_name, last_name = names[0], " ".join(names[1:])
        zoho_id = int(user_info[1])
        username = (first_name + last_name).lower()
        email = f"{first_name[0].lower()}{last_name[0].lower()}{DEFAULT_EMAIL_DOMAIN}"
        kuerzel = f"{first_name[0].upper()}{last_name[0].upper()}"
        phone = f"+49175{randint(1000000, 9999999)}"
        user_exists = User.objects.filter(zoho_id=zoho_id).exists()

        if not user_exists:
            new_user = User.objects.create(
                zoho_id=zoho_id,
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                age=30,
                phone=phone,
                is_staff=False,
                beruf="Elektriker",
                users_aufschlag=0,
                typ="keine",
                kuerzel=kuerzel,
                is_active=True,
                is_superuser=False,
            )
            new_user.set_password(f"{DEFAULT_USER_CREATION_PASSWORD}")
            new_user.save()
    else:
        print(f"Skipping user {user_info} due to incorrect data format.")


def extract_ids(data):
    return [record["ID"] for record in data["data"]]


def fetch_all_elektrik_angebots():
    headers = get_headers()
    params = {"limit": LIMIT}
    return fetch_records(BASE_URL, headers, params)


def fetch_all_detailed_elektrik_records(ids):
    headers = get_headers()
    data_list = []
    for record_id in ids:
        data = fetch_records(f"{BASE_URL}/{record_id}", headers, {})
        if data:
            data_list.append(data)
        else:
            raise APIException(f"Failed to fetch record {record_id}")
    return data_list


def extract_unique_elektrikers(json_list):
    elektriker_dict = {
        record["data"]
        .get("Elektriker", {})
        .get("display_value"): record["data"]
        .get("Elektriker", {})
        .get("ID")
        for record in json_list
        if record["data"].get("Elektriker") is not None
    }
    return json.dumps(elektriker_dict, indent=4)


def convert_dict_to_list(dict_data):
    if isinstance(dict_data, str):
        try:
            dict_data = json.loads(dict_data)
        except json.JSONDecodeError:
            raise APIException("Unable to convert string to dictionary.")
    return [[k, v] for k, v in dict_data.items()]
