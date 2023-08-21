import os
import json
import requests
from dotenv import load_dotenv, find_dotenv, set_key
from config.settings import ENV_FILE, ZOHO_ACCESS_TOKEN, ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN
from vertrieb_interface.models import VertriebAngebot

# Global constants

VERTRIEB_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"
BASE_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Elektrikkalender"
ACCESS_TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
LIMIT_ALL = 200
LIMIT_CURRENT = 10
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
    if not access_token:
        access_token = refresh_access_token()
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
    print(data)
    new_access_token = data.get("access_token")
    set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_access_token)
    return new_access_token


def handle_response(response, headers, params):
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        access_token = refresh_access_token()
        headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
        response = requests.get(VERTRIEB_URL, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data, status code: {response.status_code}")
            return None
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        return None


def fetch_all_user_angebots(request):
    user = request.user
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        access_token = refresh_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    start_index = 1
    all_user_angebots_list = []
    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_ALL,
            "criteria": f"Vertriebler.ID == {user.zoho_id}",
        }

        response = requests.get(VERTRIEB_URL, headers=headers, params=params)
        json_data = json.loads(response.text)

        with open(
            "vertrieb_interface/json_tests/all_vertriebler_angebot.json", "w"
        ) as f:
            json.dump(json_data, f)
        print("FETCH_RESPONSE # ",json_data)
        data = handle_response(response, headers, params)

        if data:
            all_user_angebots_list = process_all_user_data(data, all_user_angebots_list)

        elif response.status_code != 200:
            if response.status_code == 401:
                access_token = refresh_access_token()
                headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
                break
            else:
                print(f"Failed to fetch data, status code: {response.status_code}")
                break

        print(f"access_token is alive, status code: {response.status_code}")
        start_index += LIMIT_ALL

    return all_user_angebots_list


def fetch_current_user_angebot(request, zoho_id):
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")

    url = f"https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1/{zoho_id}"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    current_angebot_list = []

    start_index = 1

    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_CURRENT,
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            print(f"access_token is alive, status code: {response.status_code}")
            data = json.loads(response.text)
            with open(
                "vertrieb_interface/json_tests/current_vertriebler_angebot.json", "w"
            ) as f:
                json.dump(data, f)
            data_dict = data["data"]

            if not data.get("data"):
                break

            ausrichtung = data_dict.get("Dachausrichtung")
            email = data_dict.get("Email")
            angebot_bekommen_am = data_dict.get("Angebot_bekommen_am")
            verbrauch = data_dict.get("Stromverbrauch_pro_Jahr")
            leadstatus = data_dict.get("Leadstatus")
            anfrage_berr = data_dict.get("Anfrage_ber")
            notizen = data_dict.get("Notizen")
            empfohlen_von = data_dict.get("empfohlen_von")
            latitude = data_dict.get("Adresse_PVA", {}).get("latitude", "")
            longitude = data_dict.get("Adresse_PVA", {}).get("longitude", "")

            try:
                if ausrichtung in ["S\u00fcd", "Ost/West"]:
                    termin = data_dict.get("Termine")
                    current_angebot_list.append(
                        {
                            "email": email if email else "",
                            "ausrichtung": 0 if ausrichtung == "S\u00fcd" else 1,
                            "verbrauch": verbrauch if verbrauch else 15000,
                            "notizen": notizen if notizen else "",
                            "anfrage_berr": anfrage_berr if anfrage_berr else "",
                            "angebot_bekommen_am": angebot_bekommen_am
                            if angebot_bekommen_am
                            else "",
                            "empfohlen_von": empfohlen_von if empfohlen_von else "",
                            "leadstatus": leadstatus if leadstatus else "",
                            "termine_text": termin[0]["display_value"]
                            if termin[0]["display_value"]
                            else "",
                            "termine_id": termin[0]["ID"] if termin[0]["ID"] else "",
                            "latitude": latitude,
                            "longitude": longitude,
                        }
                    )
                else:
                    termin = data_dict.get("Termine")
                    current_angebot_list.append(
                        {
                            "ausrichtung": 0,
                            "email": email if email else "",
                            "angebot_bekommen_am": angebot_bekommen_am,
                            "anfrage_berr": anfrage_berr,
                            "verbrauch": verbrauch if verbrauch else 15000.0,
                            "notizen": notizen,
                            "leadstatus": leadstatus if leadstatus else "",
                            "empfohlen_von": empfohlen_von,
                            "termine_text": termin[0]["display_value"]
                            if termin[0]["display_value"]
                            else "none",
                            "termine_id": termin[0]["ID"] if termin else "",
                            "latitude": latitude,
                            "longitude": longitude,
                        }
                    )

            except:
                pass
            start_index += LIMIT_CURRENT

        if response.status_code == 401:
            print(f"Failed to fetch data, status code: {response.status_code}")
            print("Re-trying....")
            access_token = refresh_access_token()
            headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
            continue
        elif response.status_code != 200:
            print(f"Failed to fetch data, status code: {response.status_code}")
            break

    return current_angebot_list


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
