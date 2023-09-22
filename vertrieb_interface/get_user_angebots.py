import os
import json
import requests
import logging
from pprint import pprint
from time import sleep
from dotenv import load_dotenv, set_key
import datetime
from vertrieb_interface.telegram_logs_sender import send_message_to_bot
from config.settings import (
    ENV_FILE,
    ZOHO_ACCESS_TOKEN,
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    ACCESS_TOKEN_URL,
)

# Constants
BASE_URL = (
    "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report"
)
VERTRIEB_URL = f"{BASE_URL}/Privatkunden1"
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
LIMIT_ALL = 200
LIMIT_CURRENT = 200
MAX_RETRIES = 2
SLEEP_TIME = 2

# Initialize the environment
load_dotenv()
session = requests.Session()

# Exceptions
class APIException(Exception):
    pass


class UnauthorizedException(APIException):
    pass


class RateLimitExceededException(APIException):
    pass

def log_and_notify(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} - {message}")
    send_message_to_bot(message)


def get_headers():
    load_dotenv()
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    return {"Authorization": f"Zoho-oauthtoken {access_token}",}

def refresh_access_token():
    params = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive" 
    }

    response = session.post(ACCESS_TOKEN_URL, params=params, headers=headers)
    data = response.json()
    log_and_notify(f"Refresh response, \n status {response.status_code}")
    new_token = data.get("access_token")
    set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_token)
    sleep(0.5)
    
    
def fetch_data_from_api(url, params=None):
    headers = get_headers()

    for attempt in range(MAX_RETRIES):
        log_and_notify(f"Attempt {attempt + 1} to fetch data from {url} with parameters {params}")
        
        response = session.get(url, headers=headers, params=params)

        if response.status_code == HTTP_UNAUTHORIZED:
            log_and_notify("Unauthorized access, refreshing token.")
            refresh_access_token()
            access_token = os.getenv("ZOHO_ACCESS_TOKEN")
            headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
            response = session.get(url, headers=headers, params=params)
        elif response.status_code == HTTP_OK:
            log_and_notify(f"Data successfully fetched from {url}.")
            return response.json()
        else:
            log_and_notify(f"Failed to fetch data, status code: {response.status_code}. Retrying in {SLEEP_TIME} seconds.")
            sleep(SLEEP_TIME)
            
    log_and_notify(f"Exceeded maximum retry attempts for {url} with parameters {params}. Failing.")
        
def fetch_user_angebote_all(request):
    user = request.user
    start_index = 1
    all_user_angebots_list = []

    log_and_notify(f"Start fetching Angebote for user: {user.username}, User ID: {user.zoho_id}")
    
    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_ALL,
            "criteria": f"Vertriebler.ID == {user.zoho_id}",
        }

        data = fetch_data_from_api(VERTRIEB_URL, params)
        
        if data is None or not data.get("data"):
            log_and_notify(f"No more data to fetch for user: {user.username}, User ID: {user.zoho_id}. Exiting.")
            break
        else:
            all_user_angebots_list.extend(process_all_user_data(data))
            log_and_notify(f"Data page {start_index // LIMIT_ALL + 1} fetched successfully. Continuing.")
            start_index += LIMIT_ALL
            if len(data.get("data")) < LIMIT_ALL:
                break

    log_and_notify(f"Fetched all available Angebote for user: {user.username}, User ID: {user.zoho_id}")

    return all_user_angebots_list



def process_all_user_data(data):
    if not data["data"]:
        return []
    all_user_angebots_list = []

    for item in data["data"]:
        if "ID" in item:
            all_user_angebots_list.append(
                {
                    "zoho_id": item.get("ID", ""),
                    "status": item.get("Status", ""),
                    "angebot_bekommen_am": item.get("Angebot_bekommen_am", ""),
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
                    "name": item.get("Name", {}).get("last_name", "")
                    + " "
                    + item.get("Name", {}).get("suffix", "")
                    + " "
                    + item.get("Name", {}).get("first_name", ""),
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

def fetch_angenommen_status(request, zoho_id):
    url = f"{VERTRIEB_URL}/{zoho_id}"
    
    headers = get_headers()
    
    for attempt in range(MAX_RETRIES):
        log_and_notify(f"Attempt {attempt + 1} to fetch angenommen status for zoho_id: {zoho_id}")

        response = session.get(url, headers=headers)
        
        if response.status_code == HTTP_UNAUTHORIZED:
            log_and_notify("Unauthorized access, refreshing token.")
            refresh_access_token()
            sleep
            access_token = os.getenv("ZOHO_ACCESS_TOKEN")
            headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
            response = session.get(url, headers=headers)
        elif response.status_code == HTTP_OK:
            log_and_notify(f"Angenommen status successfully fetched for zoho_id: {zoho_id}")
            data = response.json()
            return data.get("data")
        else:
            log_and_notify(f"Failed to fetch angenommen status, status code: {response.status_code}. Retrying in {SLEEP_TIME} seconds.")
            sleep(SLEEP_TIME)

    log_and_notify(f"Exceeded maximum retry attempts for fetching angenommen status for zoho_id: {zoho_id}. Failing.")
    return None



def fetch_current_user_angebot(request, zoho_id):
    url = f"{VERTRIEB_URL}/{zoho_id}"

    current_angebot_list = []

    log_and_notify(f"Start fetching current user Angebot for zoho_id: {zoho_id}")
    

    data = fetch_data_from_api(url)
        
    if data:
        data_dict = data.get("data")
        if not data_dict:
            log_and_notify(f"No more data to fetch for current user Angebot for zoho_id: {zoho_id}. Exiting.")
        try:
            entry = {
                "ausrichtung": 0
                if data_dict.get("Dachausrichtung") in ["S\u00fcd", "Ost/West"]
                else 1,
                "status": data_dict.get("Status", ""),
                "email": data_dict.get("Email", ""),
                "angebot_bekommen_am": data_dict.get("Angebot_bekommen_am", ""),
                "anfrage_berr": data_dict.get("Anfrage_ber", ""),
                "notizen": data_dict.get("Notizen", ""),
                "leadstatus": data_dict.get("Leadstatus", ""),
                "empfohlen_von": data_dict.get("empfohlen_von", ""),
                "termine_text": data_dict.get("Termine", [{}])[0].get(
                    "display_value", "none"
                ),
                "termine_id": data_dict.get("Termine", [{}])[0].get("ID", ""),
                "latitude": data_dict.get("Adresse_PVA", {}).get("latitude", ""),
                "longitude": data_dict.get("Adresse_PVA", {}).get("longitude", ""),
            }
            current_angebot_list.append(entry)
            log_and_notify(f"Data page fetched successfully for current user Angebot for zoho_id: {zoho_id}. Continuing.")
        except Exception as e:
            log_and_notify(f"Error processing data for zoho_id: {zoho_id}. Error: {str(e)}")


    log_and_notify(f"Fetched all available current user Angebot for zoho_id: {zoho_id}")

    return current_angebot_list

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
                    "notizen": notizen,
                    "email": email,
                    "empfohlen_von": empfohlen_von,
                }
            )

    return current_angebot_list


def update_status(zoho_id, new_status):
    update_url = f"{VERTRIEB_URL}/{zoho_id}"

    headers = get_headers()

    current_datetime = datetime.datetime.now()
    bekommen_am = current_datetime.strftime("%d-%b-%Y")

    # Payload structured for ZOHOCreator updates (assuming it uses a 'data' key)
    payload = {
        "data": {
            "Status": new_status,
            "Angebot_bekommen_am": bekommen_am,
        }
    }

    for _ in range(2):  # Two attempts: one with the initial token and another after a refresh
        response = session.put(update_url, headers=headers, json=payload)
        
        if response.status_code == HTTP_UNAUTHORIZED:
            refresh_access_token()
            access_token = os.getenv("ZOHO_ACCESS_TOKEN")
            headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
            response = session.put(update_url, headers=headers, json=payload)
        elif response.status_code == HTTP_OK:
            return response.json()
        else:
            logging.error(f"Error updating status: {response.status_code} - {response.text}")
            send_message_to_bot(f"Updating status failed:\n{response.status_code} - {response.text}")


def return_lower_bull(val):
    return "true" if val else "false"


def pushAngebot(vertrieb_angebot, user_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/form/Angebot"
    headers = get_headers()

    date_obj_gultig = datetime.datetime.strptime(
        vertrieb_angebot.angebot_gultig, "%d.%m.%Y"
    )
    formatted_gultig_date_str = date_obj_gultig.strftime("%d-%b-%Y")

    dataMap = {
        "data": {
            "Angebot_ID": str(vertrieb_angebot.angebot_id),
            "Privatkunde_ID": str(vertrieb_angebot.zoho_id),
            "Vertriebler_ID": str(user_zoho_id),
            "erstellt_am": str(vertrieb_angebot.anfrage_vom),
            "g_ltig_bis": formatted_gultig_date_str,
            "Anz_Speicher": str(vertrieb_angebot.anz_speicher),
            "Wallbox_Typ": str(vertrieb_angebot.wallboxtyp),
            "Wallbox_Anzahl": str(vertrieb_angebot.wallbox_anzahl),
            "Kabelanschluss": str(vertrieb_angebot.kabelanschluss),
            "SolarModule_Typ": str(vertrieb_angebot.solar_module),
            "SolarModule_Leistung": str(vertrieb_angebot.modulleistungWp),
            "SolarModule_Menge": str(vertrieb_angebot.modulanzahl),
            "GarantieWR": str(vertrieb_angebot.garantieWR),
            "Eddi": "false",
            "Notstrom": return_lower_bull(vertrieb_angebot.notstrom),
            "Optimierer_Menge": str(vertrieb_angebot.anzOptimizer),
            "AC_ELWA_2": return_lower_bull(vertrieb_angebot.elwa),
            "AC_THOR": return_lower_bull(vertrieb_angebot.thor),
            "Angebotssumme": str(vertrieb_angebot.angebotsumme),
        }
    }

    for _ in range(2):  # Two attempts
        response = session.post(url, json=dataMap, headers=headers)

        if response.status_code == HTTP_OK:
            return response

        if response.status_code == HTTP_UNAUTHORIZED:
            refresh_access_token()
            access_token = os.getenv("ZOHO_ACCESS_TOKEN")
            headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
            response = session.post(url, json=dataMap, headers=headers)
        else:
            send_message_to_bot(
                f"Pushing data failed: {vertrieb_angebot.angebot_id},\n{response.status_code} - {response.text}"
            )
