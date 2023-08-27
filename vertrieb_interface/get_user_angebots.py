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
        'refresh_token': ZOHO_REFRESH_TOKEN,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
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

def fetch_user_angebote_all(request):
    user = request.user
    headers = get_headers()

    start_index = 1
    all_user_angebots_list = []
    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_ALL,
            "criteria": f"Vertriebler.ID == {user.zoho_id}",
        }

        data = fetch_data_from_api(VERTRIEB_URL, headers, params)
        if data:
            all_user_angebots_list = process_all_user_data(data, all_user_angebots_list)
        else:
            break
        start_index += LIMIT_ALL

    return all_user_angebots_list

def fetch_current_user_angebot(request, zoho_id):
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    url = f"{VERTRIEB_URL}/{zoho_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    current_angebot_list = []
    start_index = 1

    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_CURRENT,
        }

        data = fetch_data_from_api(url, headers, params)
        if data:
            with open("vertrieb_interface/json_tests/current_vertriebler_angebot.json", "w") as f:
                json.dump(data, f)
            data_dict = data["data"]
            if not data.get("data"):
                break
            try:
                entry = {
                    "ausrichtung": 0 if data_dict.get("Dachausrichtung") in ["S\u00fcd", "Ost/West"] else 1,
                    "email": data_dict.get("Email", ""),
                    "angebot_bekommen_am": data_dict.get("Angebot_bekommen_am", ""),
                    "anfrage_berr": data_dict.get("Anfrage_ber", ""),
                    "verbrauch": data_dict.get("Stromverbrauch_pro_Jahr", 15000.0),
                    "notizen": data_dict.get("Notizen", ""),
                    "leadstatus": data_dict.get("Leadstatus", ""),
                    "empfohlen_von": data_dict.get("empfohlen_von", ""),
                    "termine_text": data_dict.get("Termine", [{}])[0].get("display_value", "none"),
                    "termine_id": data_dict.get("Termine", [{}])[0].get("ID", ""),
                    "latitude": data_dict.get("Adresse_PVA", {}).get("latitude", ""),
                    "longitude": data_dict.get("Adresse_PVA", {}).get("longitude", ""),
                }
                current_angebot_list.append(entry)
            except:
                pass
            start_index += LIMIT_CURRENT
        else:
            break

    return current_angebot_list

fetch_user_angebote_all
def process_all_user_data(data, all_user_angebots_list):
    if not data["data"]:
        return all_user_angebots_list

    for item in data["data"]:
        if "ID" in item:
            all_user_angebots_list.append(
                {
                    "zoho_id": item.get("ID", ""),
                    "status": item.get("Status", ""),
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


def process_current_user_data(data, current_angebot_list):
    if not data["data"]:
        return current_angebot_list

    for data_dict in data["data"]:
        ausrichtung = data_dict.get("Dachausrichtung")
        email = data_dict.get("Email")
        verbrauch = data_dict.get("Stromverbrauch_pro_Jahr")
        notizen = data_dict.get("Notizen")
        empfohlen_von = data_dict.get("empfohlen_von")

        if ausrichtung in ["S\u00fcd", "Ost/West"]:
            current_angebot_list.append(
                {
                    "ausrichtung": 0 if ausrichtung == "S\u00fcd" else 1,
                    "verbrauch": verbrauch if verbrauch else 15000,
                    "notizen": notizen,
                    "email": email,
                    "empfohlen_von": empfohlen_von,
                }
            )

    return current_angebot_list
