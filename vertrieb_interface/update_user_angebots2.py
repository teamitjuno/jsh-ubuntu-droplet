import os, requests, json
from dotenv import set_key, load_dotenv
from config.settings import ENV_FILE

# Global constants

VERTRIEB_URL = os.getenv("BASE_URL_PRIV_KUNDEN")
REFRESH_URL = os.getenv("REFRESH_URL")
ACCESS_TOKEN_URL = os.getenv("ACCESS_TOKEN_URL")
ZOHO_ACCESS_TOKEN = os.getenv("ZOHO_ACCESS_TOKEN")
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
LIMIT_ALL = 100
LIMIT_CURRENT = 200
MAX_RETRIES = 5
SLEEP_TIME = 1

URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"

load_dotenv(ENV_FILE)

BASE_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Elektrikkalender"
ACCESS_TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
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
    access_token = ZOHO_ACCESS_TOKEN or refresh_access_token()
    return {"Authorization": f"Zoho-oauthtoken {access_token}"}


def id_and_name_extractor(data):
    for entry in data:
        zoho_id = entry.get("zoho_id", None)
        name = entry.get("name", None)
        print(f"ZohoAngebotID:  {zoho_id},  Name: {name}")


def refresh_access_token():
    params = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    response = requests.post(ACCESS_TOKEN_URL, params=params)

    if response.status_code != HTTP_OK:
        raise APIException(f"Error refreshing token: {response.status_code}")

    new_access_token = response.json().get("access_token")
    set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_access_token)
    return new_access_token


def process_all_user_data(data, all_user_angebots_list):
    if not data["data"]:
        return all_user_angebots_list

    for item in data["data"]:
        if "ID" in item:
            all_user_angebots_list.append(
                {
                    "zoho_id": item.get("ID", ""),
                    "anrede": item.get("Name", {}).get("prefix", ""),
                    "strasse": item.get("Adresse_PVA", {}).get("address_line_1", ""),
                    "ort": item.get("Adresse_PVA", {}).get("postal_code", "")
                    + " "
                    + item.get("Adresse_PVA", {}).get("district_city", ""),
                    "postanschrift_longitude": item.get("Adresse_PVA", {}).get(
                        "longitude", ""
                    ),
                    "postanschrift_latitude": item.get("Adresse_PVA", {}).get(
                        "latitude", ""
                    ),
                    "telefon_festnetz": item.get("Telefon_Festnetz", ""),
                    "telefon_mobil": item.get("Telefon_mobil", ""),
                    "zoho_kundennumer": item.get("Kundennummer", ""),
                    "email": item.get("Email", ""),
                    "notizen": item.get("Notizen", ""),
                    "name": item.get("Name", {}).get("first_name", "")
                    + " "
                    + item.get("Name", {}).get("suffix", "")
                    + " "
                    + item.get("Name", {}).get("last_name", ""),
                    "vertriebler_display_value": item.get("Vertriebler", {}).get(
                        "display_value", ""
                    ),
                    "vertriebler_id": item.get("Vertriebler", {}).get("ID", ""),
                    "adresse_pva_display_value": item.get("Adresse_PVA", {}).get(
                        "display_value", ""
                    ),
                    "anfrage_vom": item.get("Anfrage_vom", ""),
                }
            )
    return all_user_angebots_list
