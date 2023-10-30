import os
import json
import time
import requests
from dotenv import load_dotenv, set_key
import datetime
from vertrieb_interface.telegram_logs_sender import send_message_to_bot
from config.settings import (
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    ACCESS_TOKEN_URL,
)

BASE_URL = (
    "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report"
)
VERTRIEB_URL = f"{BASE_URL}/Privatkunden1"
ANGEBOTE_URL = f"{BASE_URL}/Angebote"
PROVISIONE_URL = f"{BASE_URL}/Provision_alle_PVA"
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
LIMIT_ALL = 200
LIMIT_CURRENT = 200
MAX_RETRIES = 2
SLEEP_TIME = 2

load_dotenv()
session = requests.Session()


class APIException(Exception):
    pass


class UnauthorizedException(APIException):
    pass


class RateLimitExceededException(APIException):
    pass


token_info = {"access_token": None, "expires_at": 0}


def refresh_access_token():
    """
    Refresh the access token using the refresh token.
    """
    global token_info

    current_time = time.time()
    if current_time < token_info["expires_at"]:
        return token_info["access_token"]

    token_data = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    try:
        response = requests.post(ACCESS_TOKEN_URL, data=token_data)
        response.raise_for_status()

        token_info["access_token"] = response.json()["access_token"]
        token_info["expires_at"] = current_time + response.json()["expires_in"]

        log_and_notify(
            f"Access token refreshed successfully. Expires at: {token_info['expires_at']}"
        )

        return token_info["access_token"]
    except:
        log_and_notify(f"Error refreshing access token")


def log_and_notify(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")
    send_message_to_bot(message)


def fetch_data_from_api(url, params=None):
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    # log_and_notify(f"Attempt to fetch data with parameters {params}")

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == HTTP_OK:
        log_and_notify(f"Data successfully fetched.")
        return response.json()
    else:
        log_and_notify(
            f"Failed to fetch data, status code: {response.status_code}. Retrying in {SLEEP_TIME} seconds."
        )
        time.sleep(SLEEP_TIME)

    return None


def fetch_user_angebote_all(request):
    user = request.user
    start_index = 1
    all_user_angebots_list = []

    log_and_notify(
        f"Start fetching Angebote for user: {user.username}, User ID: {user.zoho_id}"
    )

    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_ALL,
            "criteria": f"Vertriebler.ID == {user.zoho_id}",
        }

        data = fetch_data_from_api(VERTRIEB_URL, params)

        if data is None or not data.get("data"):
            log_and_notify(
                f"No more data to fetch for user: {user.username}, User ID: {user.zoho_id}. Exiting."
            )
            break
        else:
            all_user_angebots_list.extend(process_all_user_data(data))
            log_and_notify(
                f"Data page {start_index // LIMIT_ALL + 1} fetched successfully. Continuing."
            )
            start_index += LIMIT_ALL
            if len(data.get("data")) < LIMIT_ALL:
                break

    log_and_notify(
        f"Fetched all available Angebote for user: {user.username}, User ID: {user.zoho_id}"
    )

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
    user = request.user
    url = f"{VERTRIEB_URL}/{zoho_id}"

    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # log_and_notify(
    #     f"{user.email} Attempt to fetch angenommen status for zoho_id: {zoho_id}"
    # )

    response = requests.get(url, headers=headers)
    data = response.json()
    data = data.get("data")
    return data


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

    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    current_datetime = datetime.datetime.now()
    bekommen_am = current_datetime.strftime("%d-%b-%Y")

    payload = {
        "data": {
            "Status": new_status,
            "Angebot_bekommen_am": bekommen_am,
        }
    }

    response = requests.put(update_url, headers=headers, json=payload)
    return response.json()


def return_lower_bull(val):
    return "true" if val else "false"


def pushAngebot(vertrieb_angebot, user_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/form/Angebot"
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

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
            "Wechselrichter": str(vertrieb_angebot.wechselrichter_model),
            "Speicher_Typ": str(vertrieb_angebot.speicher_model),
            "Wandhalterung_Anzahl": int(
                vertrieb_angebot.anz_wandhalterung_fuer_speicher
            ),
            "Notstrom": return_lower_bull(vertrieb_angebot.notstrom),
            "Optimierer_Menge": str(vertrieb_angebot.anzOptimizer),
            "AC_ELWA_2": return_lower_bull(vertrieb_angebot.elwa),
            "AC_THOR": return_lower_bull(vertrieb_angebot.thor),
            "AC_THOR_Heizstab": vertrieb_angebot.heizstab,
            "Zahlungsmodalit_ten": str(vertrieb_angebot.zahlungsbedingungen),
            "Angebotssumme": str(vertrieb_angebot.angebotsumme),
        }
    }
    response = requests.post(url, json=dataMap, headers=headers)
    response_data = response.json()
    new_record_id = response_data["data"]["ID"]
    log_and_notify(f"New record ID: {new_record_id}")

    return response


import requests


def delete_redundant_angebot(angebot_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Angebote/{angebot_zoho_id}"
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.delete(url, headers=headers)
    if not response:
        log_and_notify(
            f"Failed to delete record with ID {angebot_zoho_id}. Response: {response.text}"
        )
        pass
    else:
        log_and_notify(f"Record with ID {angebot_zoho_id} deleted successfully")
        pass


def fetch_angebote_all():
    all_provisione_list = []
    data = fetch_data_from_api(ANGEBOTE_URL)
    all_provisione_list.extend(data)
    return data


def fetch_provisione_all():
    all_provisione_list = []
    data = fetch_data_from_api(PROVISIONE_URL)
    all_provisione_list.extend(data)
    return data


def extract_values(request):
    user = request.user
    input_json = fetch_angebote_all()
    parsed_data = input_json
    target_vertriebler_id = f"{user.zoho_id}"

    # Filter the data
    filtered_angebote_data = [
        item
        for item in parsed_data["data"]
        if item["Vertriebler_ID"]["ID"] == target_vertriebler_id
    ]

    input_json = fetch_provisione_all()
    parsed_data = input_json
    filtered_provisione_data = [
        item
        for item in parsed_data["data"]
        if item["Vertriebler"]["ID"] == target_vertriebler_id
    ]
    angebotsumme_list = [
        item["Rechnungsh_he_netto_laut_Angebot"] for item in filtered_provisione_data
    ]

    filtered_existing_angebote_result_data = [
        item
        for item in filtered_angebote_data
        if item["Angebotssumme"] in angebotsumme_list
    ]
    existing_angebot_ids = [
        item["Angebot_ID"] for item in filtered_existing_angebote_result_data
    ]

    log_and_notify(f"{angebotsumme_list}")
    log_and_notify(f"{existing_angebot_ids}")

    return existing_angebot_ids
