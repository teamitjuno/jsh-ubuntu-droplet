import os
import json
import requests
from dotenv import load_dotenv, find_dotenv, set_key
from config.settings import (
    ENV_FILE,
    ZOHO_ACCESS_TOKEN,
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
)
from vertrieb_interface.models import VertriebAngebot

VERTRIEB_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"
BASE_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Elektrikkalender"
ACCESS_TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
LIMIT_ALL = 200
LIMIT_CURRENT = 200
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


def fetch_data_from_api(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == HTTP_OK:
        return response.json()
    elif response.status_code == HTTP_UNAUTHORIZED:
        headers["Authorization"] = f"Zoho-oauthtoken {refresh_access_token()}"
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == HTTP_OK:
            return response.json()
    return None


def post_angebot_to_zoho(vertrieb_angebot, request_user):
    """
    Send a POST request to the specified Zoho endpoint.
    """
    # Endpoint URL
    url = "https://creator.zoho.eu/appbuilder/thomasgroebckmann/juno-kleinanlagen-portal/form/Angebot"

    # Headers for the request
    headers = get_headers()

    # Data structure
    payload = {
        "code": 3000,
        "data": {
            "Angebot_ID": vertrieb_angebot.angebot_id,
            "Privatkunde_ID": vertrieb_angebot.zoho_id,
            "Vertriebler_ID": request_user.zoho_id,
            "erstellt_am": vertrieb_angebot.angebot_bekommen_am,
            "g_ltig_bis": vertrieb_angebot.angebot_gultig,
            "Anz_Speicher": vertrieb_angebot.anz_speicher,
            "Wallbox_Typ": vertrieb_angebot.wallboxtyp,
            "Wallbox_Anzahl": vertrieb_angebot.wallbox_anzahl,
            "Kabelanschluss": vertrieb_angebot.kabelanschluss,
            "SolarModule_Typ": vertrieb_angebot.solar_module,
            "SolarModule_Leistung": vertrieb_angebot.modulleistungWp,
            "SolarModule_Menge": vertrieb_angebot.modulanzahl,
            "GarantieWR": vertrieb_angebot.garantieWR,
            "Eddi": "false",
            "Notstrom": vertrieb_angebot.notstrom,
            "Optimierer_Menge": vertrieb_angebot.anzOptimizer,
            "AC_ELWA_2": vertrieb_angebot.elwa,
            "AC_THOR": vertrieb_angebot.thor,
            "Angebotssumme": vertrieb_angebot.angebotsumme,
        },
    }

    # Send the POST request
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != HTTP_OK:
        raise APIException(
            f"Error updating status: {response.status_code} - {response.text}"
        )

    return response.json()
