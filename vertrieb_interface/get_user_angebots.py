import os
import json
import requests
from time import sleep
from dotenv import load_dotenv, set_key
from django.utils import timezone
import datetime
from django.utils.formats import date_format
from config.settings import (
    ENV_FILE,
    ZOHO_ACCESS_TOKEN,
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
)
load_dotenv()
VERTRIEB_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"
BASE_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Elektrikkalender"
ACCESS_TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_UNAUTHORIZED = 401
LIMIT_ALL = 200
LIMIT_CURRENT = 200
MAX_RETRIES = 9
SLEEP_TIME = 1
now = timezone.now()
now_german = date_format(now, "DATETIME_FORMAT")


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
    retry_count = 0
    new_access_token = None

    while new_access_token is None and retry_count < MAX_RETRIES:
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
        sleep(2)
        retry_count += 1

    if new_access_token is None:
        raise APIException("Failed to retrieve a new access token after maximum retries.")

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


def fetch_angenommen_status(request, zoho_id):
    
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    url = f"{VERTRIEB_URL}/{zoho_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    current_angebot_list = []
    start_index = 1

    params = {
        "from": start_index,
        "limit": LIMIT_CURRENT,
    }

    data = fetch_data_from_api(url, headers, params)

    if data:
        with open(
            "vertrieb_interface/json_tests/current_vertriebler_angebot.json", "w"
        ) as f:
            json.dump(data, f)
    data_dict = data["data"]
    return data_dict


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
            with open(
                "vertrieb_interface/json_tests/current_vertriebler_angebot.json", "w"
            ) as f:
                json.dump(data, f)
            data_dict = data["data"]

            if not data.get("data"):
                break
            try:
                entry = {
                    "ausrichtung": 0
                    if data_dict.get("Dachausrichtung") in ["S\u00fcd", "Ost/West"]
                    else 1,
                    "status": data_dict.get("Status", ""),
                    "email": data_dict.get("Email", ""),
                    "angebot_bekommen_am": data_dict.get("Angebot_bekommen_am", ""),
                    "anfrage_berr": data_dict.get("Anfrage_ber", ""),
                    "verbrauch": data_dict.get("Stromverbrauch_pro_Jahr", 15000.0),
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
            except:
                pass
            start_index += LIMIT_CURRENT
        else:
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
    print(current_angebot_list)

    return current_angebot_list

def update_status(zoho_id, new_status):
    """
    Update the 'Status' field of a given Zoho record.

    :param zoho_id: The ID of the record you want to update.
    :param new_status: The new value for the 'Status' field.
    :return: The server's response to the POST request or None if there's an error.
    """
    
    # Endpoint for updating
    update_url = f"{VERTRIEB_URL}/{zoho_id}"

    # Headers for the request
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

    # Making the POST request
    response = requests.put(update_url, headers=headers, json=payload)

    # If Unauthorized, refresh token and retry
    if response.status_code == HTTP_UNAUTHORIZED:
        headers["Authorization"] = f"Zoho-oauthtoken {refresh_access_token()}"
        response = requests.put(update_url, headers=headers, json=payload)

    # Handling the response
    if response.status_code != HTTP_OK:
        raise APIException(
            f"Error updating status: {response.status_code} - {response.text}"
        )

    return response.json()





def post_data_to_api(url, headers, data):
    response = requests.post(url, headers=headers, json=data)

    if response.status_code in [HTTP_OK, HTTP_CREATED]:
        return response.json()

    if response.status_code == HTTP_UNAUTHORIZED:
        headers["Authorization"] = f"Zoho-oauthtoken {refresh_access_token()}"
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [HTTP_OK, HTTP_CREATED]:
            return response.json()

    raise APIException(f"Error posting: {response.status_code} - {response.text}")


def post_angebot_to_zoho(form):
    """
    Send a POST request to the specified Zoho endpoint.
    """
    vertrieb_angebot = form
    url = f"https://creator.zoho.eu/appbuilder/thomasgroebckmann/juno-kleinanlagen-portal/form/Angebot"
    headers = get_headers()

    # Format the 'angebot_gultig' date
    date_gultig_str = vertrieb_angebot.angebot_gultig
    date_obj_gultig = datetime.datetime.strptime(date_gultig_str, "%d.%m.%Y")
    formatted_gultig_date_str = date_obj_gultig.strftime("%d-%b-%Y")

    Privatkunde_ID = int(vertrieb_angebot.zoho_id)
    Anz_Speicher = int(vertrieb_angebot.anz_speicher)
    Wallbox_Anzahl = int(vertrieb_angebot.wallbox_anzahl)
    Kabelanschluss = float(vertrieb_angebot.wallbox_anzahl)
    SolarModule_Leistung = int(vertrieb_angebot.modulleistungWp)
    SolarModule_Menge = int(vertrieb_angebot.modulanzahl)
    Angebotssumme = float(vertrieb_angebot.angebotsumme)
    Optimierer_Menge = int(vertrieb_angebot.anzOptimizer)

    # Data structure
    print(type(vertrieb_angebot.angebot_id), vertrieb_angebot.angebot_id)
    print(type(vertrieb_angebot.zoho_id), vertrieb_angebot.zoho_id)
    print(type(vertrieb_angebot.current_date), vertrieb_angebot.current_date)
    print(type(vertrieb_angebot.anfrage_vom), vertrieb_angebot.anfrage_vom)

    print(
        type(vertrieb_angebot.angebot_bekommen_am), vertrieb_angebot.angebot_bekommen_am
    )
    print(type(vertrieb_angebot.angebot_gultig), vertrieb_angebot.angebot_gultig)
    print(type(vertrieb_angebot.anz_speicher), vertrieb_angebot.anz_speicher)
    print(type(vertrieb_angebot.wallboxtyp), vertrieb_angebot.wallboxtyp)
    print(type(vertrieb_angebot.wallbox_anzahl), vertrieb_angebot.wallbox_anzahl)
    print(type(vertrieb_angebot.kabelanschluss), vertrieb_angebot.kabelanschluss)
    print(type(vertrieb_angebot.solar_module), vertrieb_angebot.solar_module)
    print(type(vertrieb_angebot.modulleistungWp), vertrieb_angebot.modulleistungWp)
    print(type(vertrieb_angebot.modulanzahl), vertrieb_angebot.modulanzahl)
    print(type(vertrieb_angebot.garantieWR), vertrieb_angebot.garantieWR)
    print(type(vertrieb_angebot.notstrom), vertrieb_angebot.notstrom)
    print(type(vertrieb_angebot.anzOptimizer), vertrieb_angebot.anzOptimizer)
    print(type(vertrieb_angebot.elwa), vertrieb_angebot.elwa)
    print(type(vertrieb_angebot.thor), vertrieb_angebot.thor)
    print(type(vertrieb_angebot.angebotsumme), vertrieb_angebot.angebotsumme)

    payload = {
        "Angebot_ID": f"{vertrieb_angebot.angebot_id}",
        "Privatkunde_ID": Privatkunde_ID,
        "Anz_Speicher": Anz_Speicher,
        "erstellt_am": vertrieb_angebot.anfrage_vom,
        "g_ltig_bis": formatted_gultig_date_str,
        "Wallbox_Typ": f"{vertrieb_angebot.wallboxtyp}",
        "Wallbox_Anzahl": Wallbox_Anzahl,
        "Kabelanschluss": Kabelanschluss,
        "SolarModule_Typ": f"{vertrieb_angebot.solar_module}",
        "SolarModule_Leistung": SolarModule_Leistung,
        "SolarModule_Menge": SolarModule_Menge,
        "GarantieWR": f"{vertrieb_angebot.garantieWR}",
        "Eddi": False,
        "Notstrom": vertrieb_angebot.notstrom,
        "Optimierer_Menge": Optimierer_Menge,
        "AC_ELWA_2": vertrieb_angebot.elwa,
        "AC_THOR": vertrieb_angebot.thor,
        "Angebotssumme": Angebotssumme,
    }

    new_payload = {"Angebote": [payload]}

    response = post_data_to_api(url, headers, new_payload)

    return response

def return_lower_bull(val):
    if val == True:
        return "true"
    else:
        return "false"

def pushAngebot(vertrieb_angebot, user_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/form/Angebot"
    headerMap = get_headers()

    date_gultig_str = vertrieb_angebot.angebot_gultig
    date_obj_gultig = datetime.datetime.strptime(date_gultig_str, "%d.%m.%Y")
    formatted_gultig_date_str = date_obj_gultig.strftime("%d-%b-%Y")
    notstrom = return_lower_bull(vertrieb_angebot.notstrom)
    elwa = return_lower_bull(vertrieb_angebot.elwa)
    thor = return_lower_bull(vertrieb_angebot.thor)

    dataMap = {"data": {
      "Angebot_ID":f"{vertrieb_angebot.angebot_id}",
      "Privatkunde_ID":f"{vertrieb_angebot.zoho_id}",
      "Vertriebler_ID":f"{user_zoho_id}",
      "erstellt_am":f"{vertrieb_angebot.anfrage_vom}",
      "g_ltig_bis":f"{formatted_gultig_date_str}",
      "Anz_Speicher":f"{vertrieb_angebot.anz_speicher}",
      "Wallbox_Typ":f"{vertrieb_angebot.wallboxtyp}",
      "Wallbox_Anzahl":f"{vertrieb_angebot.wallbox_anzahl}",
      "Kabelanschluss":f"{vertrieb_angebot.kabelanschluss}",
      "SolarModule_Typ":f"{vertrieb_angebot.solar_module}",
      "SolarModule_Leistung":f"{vertrieb_angebot.modulleistungWp}",
      "SolarModule_Menge":f"{vertrieb_angebot.modulanzahl}",
      "GarantieWR":f"{vertrieb_angebot.garantieWR}",
      "Eddi":"false",
      "Notstrom":notstrom,
      "Optimierer_Menge":f"{vertrieb_angebot.anzOptimizer}",
      "AC_ELWA_2":elwa,
      "AC_THOR":thor,
      "Angebotssumme":f"{vertrieb_angebot.angebotsumme}",
       }
    }
    
    response = requests.post(url, json=dataMap,headers=headerMap)
    # If Unauthorized, refresh token and retry
    print(response)
    if response.status_code == HTTP_UNAUTHORIZED:
        headerMap["Authorization"] = f"Zoho-oauthtoken {refresh_access_token()}"
        response = requests.post(url, headers=headerMap, json=dataMap)

    # Handling the response
    if response.status_code != HTTP_OK:
        raise APIException(
            f"Error updating status: {response.status_code} - {response.text}"
        )
    
    return response