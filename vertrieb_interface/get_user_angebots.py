import time
import requests
from dotenv import load_dotenv, set_key
import datetime
import requests
from django.core.exceptions import ValidationError
import json
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

        return token_info["access_token"]
    except:
        print(f"Error refreshing access token")


def log_and_notify(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")
    timelaps = (f"{message} - {timestamp}")
    send_message_to_bot(f'{timelaps}')


def fetch_data_from_api(url, params=None):
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == HTTP_OK:
        
        return response.json()
    else:
        
        time.sleep(SLEEP_TIME)

    return None


def fetch_user_angebote_all(request):
    user = request.user
    start_index = 1
    all_user_angebots_list = []

    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_ALL,
            "criteria": f"Vertriebler.ID == {user.zoho_id}",
        }

        data = fetch_data_from_api(VERTRIEB_URL, params)

        if data is None or not data.get("data"):

            break
        else:
            all_user_angebots_list.extend(process_all_user_data(data))

            start_index += LIMIT_ALL
            if len(data.get("data")) < LIMIT_ALL:
                break



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
                    + ""
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


def put_form_data_to_zoho_jpp(form):
    # Extract data from form
    form_data = {field: form.cleaned_data.get(field) for field in form.fields}

    zoho_id = form_data.get('zoho_id')
    vorname_nachname = form_data.get('vorname_nachname')

    if not zoho_id:
        raise ValueError("Zoho ID and new status are required")

    update_url = f"{VERTRIEB_URL}/{zoho_id}"
    
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    bekommen_am = datetime.datetime.now().strftime("%d-%b-%Y")
    anrede = form_data.get('anrede')
    name_parts = vorname_nachname.split()
    log_and_notify(name_parts)
    if len(name_parts) == 2:
        last_name = name_parts[0]
        first_name = name_parts[1]
        middle_name = ''
        postal_code = " ".join(form_data.get("ort").split(" ")[:-1]),
        district_city = form_data.get('ort').split(' ')[1],
        strasse = form_data.get('strasse'),
        display_value = f"{anrede}" + " " + f"{first_name}" + " " + f"{' '.join([middle_name, last_name]).strip()}"
        log_and_notify(first_name)
        log_and_notify(last_name)
        log_and_notify(display_value)
        payload = {
        "data": {
            "Email": form_data.get('email'),
            "Telefon_Festnetz": form_data.get('telefon_festnetz'),
            "Telefon_mobil": form_data.get('telefon_mobil'),
            "Name": {
                # "display_value": display_value,
                "prefix": anrede,
                "suffix": middle_name,
                "last_name": last_name,
                "first_name": first_name,
            },
            "Adresse_PVA": {
                # "display_value": f"{form_data.get('strasse')}, {form_data.get('ort')}",
                "district_city": district_city[0],
                "address_line_1": strasse[0],
                "postal_code": postal_code[0],
            },
        }
    }
        json_payload = json.dumps(payload, ensure_ascii=True)
        headers['Content-Type'] = 'application/json'
        log_and_notify(type(json_payload))
        log_and_notify(type(payload))
        log_and_notify(json_payload)
        str_payload = f"{json_payload}"
        response = requests.put(update_url, headers=headers, json=str_payload)
        log_and_notify(response)
        res = response.json()
        log_and_notify(res)
        return response.json()
    
    elif len(name_parts) == 3:
        last_name = name_parts[0]
        first_name = name_parts[1]
        middle_name = name_parts[-1]



        # Constructing the payload for the API
        payload = {
            "data": {
                "Email": form_data.get('email'),
                "Telefon_Festnetz": form_data.get('telefon_festnetz'),
                "Telefon_mobil": form_data.get('telefon_mobil'),
                "Name": {
                    # "display_value": f"{anrede} {first_name} {' '.join([middle_name, last_name]).strip()}",
                    "prefix": f"{anrede}",
                    "suffix": f"{middle_name}",
                    "last_name": f"{last_name}",
                    "first_name": f"{first_name}",
                },
                "Adresse_PVA": {
                    # "display_value": f"{form_data.get('strasse')}, {form_data.get('ort')}",
                    "district_city": district_city,
                    "address_line_1": strasse,
                    "postal_code": postal_code,
                },
            }
        }


        response = requests.put(update_url, headers=headers, json=payload)

        return response.json()

# def put_form_data_to_zoho_jpp(form):
#     # Extrahieren der Formulardaten
#     form_data = {field: form.cleaned_data.get(field) for field in form.fields}
#     zoho_id = form_data.get('zoho_id')
#     vorname_nachname = form_data.get('vorname_nachname')

#     if not zoho_id or not vorname_nachname:
#         raise ValueError("Zoho ID und Vorname Nachname sind erforderlich")

#     # Vorbereitung der API-Anfrage
#     update_url = f"{VERTRIEB_URL}/{zoho_id}"
#     access_token = refresh_access_token()
#     headers = {"Authorization": f"Bearer {access_token}"}

#     # Aufbereitung der Namensteile
#     name_parts = vorname_nachname.split()
#     if len(name_parts) < 2:
#         raise ValidationError("Vorname und Nachname sind erforderlich")
#     first_name, last_name = name_parts[1], name_parts[0]
#     middle_name = name_parts[2] if len(name_parts) == 3 else ''

#     # Konstruktion des Payloads
#     payload = {
#         "data": {
#             "Email": form_data.get('email'),
#             "Telefon_Festnetz": form_data.get('telefon_festnetz'),
#             "Telefon_mobil": form_data.get('telefon_mobil'),
#             "Name": {
#                 "display_value": f"{form_data.get('anrede')} {first_name} {' '.join([middle_name, last_name]).strip()}",
#                 "prefix": form_data.get('anrede'),
#                 "suffix": middle_name,
#                 "last_name": last_name,
#                 "first_name": first_name,
#             },
#             "Adresse_PVA": {
#                 "display_value": f"{form_data.get('strasse')}, {form_data.get('ort')}",
#                 "district_city1": form_data.get('ort').split(' ')[1],
#                 "address_line_1": form_data.get('strasse'),
#                 "postal_code": ' '.join(form_data.get('ort').split(' ')[:-1]),
#             },
#         }
#     }
#     log_and_notify(payload)

#     # Senden der Anfrage
#     response = requests.put(update_url, headers=headers, json=payload)
#     if response.status_code != 200:
#         raise ValueError("Fehler beim Aktualisieren des Zoho-Eintrags")
#     res = f'{response.json()}'
#     log_and_notify(res)
#     return response.json()

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
    log_and_notify(f"Neue Angebot nach Zoho gesendet record ID: {new_record_id}, Angebotssumme: {vertrieb_angebot.angebotsumme}")

    return response


import requests


def delete_redundant_angebot(angebot_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Angebote/{angebot_zoho_id}"
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.delete(url, headers=headers)
    if not response:

        pass
    else:
        
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


    return existing_angebot_ids
