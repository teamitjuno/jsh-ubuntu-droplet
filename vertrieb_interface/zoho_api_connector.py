import time
import requests
from dotenv import load_dotenv
import datetime
import requests
import json
from vertrieb_interface.telegram_logs_sender import send_message_to_bot
from config.settings import (
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    ACCESS_TOKEN_URL,
    BASE_URL,
)

VERTRIEB_URL = f"{BASE_URL}/Privatkunden_API"
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
    if user.role.name == "admin" or user.role.name == "manager":
        crit = f'Vertriebler.ID != null && Anfrage_vom > today.subDay({user.records_fetch_limit}) && (Status == null || Status == "" || (Status != "storniert" && Status != "abgelehnt" && Status != "nicht qualifiziert"))'
    else:
        crit = f'Vertriebler.ID == {user.zoho_id} && Anfrage_vom > today.subDay({user.records_fetch_limit}) && (Status == null || Status == "" || (Status != "storniert" && Status != "abgelehnt" && Status != "nicht qualifiziert"))'
    while True:
        params = {
            "from": start_index,
            "limit": LIMIT_ALL,
            "criteria": crit,
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


def log_and_notify(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timelaps = f"{message} - {timestamp}"
    send_message_to_bot(f"{timelaps}")


def process_all_user_data(data):
    if not data["data"]:
        return []
    all_user_angebots_list = []

    for item in data["data"]:
        if "ID" in item and item.get("Name", {}).get("prefix", "") == "Firma":

            all_user_angebots_list.append(
                {
                    "zoho_id": item.get("ID", ""),
                    "status": item.get("Status", ""),
                    "status_pva": item.get("Status_PVA", ""),
                    "angebot_bekommen_am": item.get("Angebot_bekommen_am", ""),
                    "anrede": item.get("Name", {}).get("prefix", ""),
                    "strasse": item.get("Adresse_PVA", {}).get("address_line_1", ""),
                    "ort": item.get("Adresse_PVA", {}).get("postal_code", "")
                    + " "
                    + item.get("Adresse_PVA", {}).get("district_city", ""),
                    "postanschrift_name": item.get("Name_Postanschrift", {}).get("prefix", "")
                    + " " + item.get("Name_Postanschrift", {}).get("first_name", "")
                    + " " + item.get("Name_Postanschrift", {}).get("last_name", ""),
                    "postanschrift": item.get("Postanschrift", {}).get("address_line_1", ""),
                    "postanschrift_ort": item.get("Postanschrift", {}).get("postal_code", "")
                    + " " + item.get("Postanschrift", {}).get("district_city", ""),
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
                    "name": item.get("Name", {}).get("last_name", ""),
                    "name_first_name": item.get("Name", {}).get("first_name", ""),
                    "name_last_name": item.get("Name", {}).get("last_name", ""),
                    "name_suffix": item.get("Name", {}).get("suffix", ""),
                    "vertriebler_display_value": item.get("Vertriebler", {}).get(
                        "display_value", ""
                    ),
                    "vertriebler_id": item.get("Vertriebler", {}).get("ID", ""),
                    "adresse_pva_display_value": item.get("Adresse_PVA", {}).get(
                        "display_value", ""
                    ),
                    "anfrage_vom": item.get("Anfrage_vom", ""),
                    "angebot": (
                        item.get("Angebot", [])[0].get("display_value", "")
                        if item.get("Angebot") != ""
                        else ""
                    ),
                    "angenommenes_angebot": item.get("Angenommenes_Angebot", ""),
                }
            )
        else:
            all_user_angebots_list.append(
                {
                    "zoho_id": item.get("ID", ""),
                    "status": item.get("Status", ""),
                    "status_pva": item.get("Status_PVA", ""),
                    "angebot_bekommen_am": item.get("Angebot_bekommen_am", ""),
                    "anrede": item.get("Name", {}).get("prefix", ""),
                    "strasse": item.get("Adresse_PVA", {}).get("address_line_1", ""),
                    "ort": item.get("Adresse_PVA", {}).get("postal_code", "")
                    + " "
                    + item.get("Adresse_PVA", {}).get("district_city", ""),
                    "postanschrift_name": item.get("Name_Postanschrift", {}).get("prefix", "")
                    + " " + item.get("Name_Postanschrift", {}).get("first_name", "")
                    + " " + item.get("Name_Postanschrift", {}).get("last_name", ""),
                    "postanschrift": item.get("Postanschrift", {}).get("address_line_1", ""),
                    "postanschrift_ort": item.get("Postanschrift", {}).get("postal_code", "")
                    + " " + item.get("Postanschrift", {}).get("district_city", ""),
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
                    + ", "
                    + item.get("Name", {}).get("suffix", "")
                    + ""
                    + item.get("Name", {}).get("first_name", ""),
                    "name_first_name": item.get("Name", {}).get("first_name", ""),
                    "name_last_name": item.get("Name", {}).get("last_name", ""),
                    "name_suffix": item.get("Name", {}).get("suffix", ""),
                    "vertriebler_display_value": item.get("Vertriebler", {}).get(
                        "display_value", ""
                    ),
                    "vertriebler_id": item.get("Vertriebler", {}).get("ID", ""),
                    "adresse_pva_display_value": item.get("Adresse_PVA", {}).get(
                        "display_value", ""
                    ),
                    "anfrage_vom": item.get("Anfrage_vom", ""),
                    "angebot": (
                        item.get("Angebot", [])[0].get("display_value", "")
                        if item.get("Angebot") != ""
                        else ""
                    ),
                    "angenommenes_angebot": item.get("Angenommenes_Angebot", ""),
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


def escape_unicode_chars(s):
    """
    Manually replace specific unicode characters with their escape sequences.
    This is a simple implementation and might need to be extended based on actual use cases.
    """
    replacements = {
        "ö": "\\u00f6",
        "ä": "\\u00e4",
        "ü": "\\u00fc",
        # Add more replacements as needed
    }
    for original, escape in replacements.items():
        s = s.replace(original, escape)
    return s


def put_form_data_to_zoho_jpp(form):
    # Extract data from form
    form_data = {field: form.cleaned_data.get(field) for field in form.fields}

    zoho_id = form_data.get("zoho_id")
    vorname_nachname = form_data.get("vorname_nachname")
    vorname_nachname = escape_unicode_chars(vorname_nachname)

    if not zoho_id:
        raise ValueError("Zoho ID and new status are required")

    update_url = f"{VERTRIEB_URL}/{zoho_id}"

    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    anrede = form_data.get("anrede")
    name_first_name = form_data.get("name_first_name")
    name_suffix = form_data.get("name_suffix")
    name_last_name = form_data.get("name_last_name")
    longitude = form_data.get("postanschrift_longitude")
    latitude = form_data.get("postanschrift_latitude")

    postal_code = (" ".join(form_data.get("ort").split(" ")[:-1]),)
    district_city = (form_data.get("ort").split(" ")[1],)
    strasse = (form_data.get("strasse"),)

    payload = {
        "data": {
            "Email": form_data.get("email"),
            "Telefon_Festnetz": form_data.get("telefon_festnetz"),
            "Telefon_mobil": form_data.get("telefon_mobil"),
            "Name": {
                "display_value": f"{anrede} {name_last_name} {name_suffix} {name_first_name}",
                "prefix": f"{anrede}",
                "last_name": f"{name_last_name}",
                "suffix": f"{name_suffix}",
                "first_name": f"{name_first_name}",
            },
            "Adresse_PVA": {
                "district_city": district_city[0],
                "address_line_1": strasse[0],
                "postal_code": postal_code[0],
                "longitude": longitude,
                "latitude": latitude,
            },
        }
    }

    headers["Content-Type"] = "application/json"

    response = requests.patch(update_url, headers=headers, json=payload)

    return response.json()


def return_lower_bull(val):
    return "true" if val else "false"


def pushAngebot(vertrieb_angebot, user_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/junosolar/juno-kleinanlagen-portal/form/Angebot"
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    date_obj_gultig = datetime.datetime.strptime(
        vertrieb_angebot.angebot_gultig, "%d.%m.%Y"
    )
    formatted_gultig_date_str = date_obj_gultig.strftime("%d-%b-%Y")

    dataMap = {
        "data": {
            "Angebot_ID": str(vertrieb_angebot.angebot_id),
            "Typ": "Angebot PV",
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
            "Smartmeter_Typ":str(vertrieb_angebot.smartmeter_model),
            "Wandhalterung_Anzahl": int(
                vertrieb_angebot.anz_wandhalterung_fuer_speicher
            ),
            "Notstrom": return_lower_bull(vertrieb_angebot.notstrom),
            "Ersatzstrom": return_lower_bull(vertrieb_angebot.ersatzstrom),
            "Optimierer_Menge": str(vertrieb_angebot.anzOptimizer),
            "AC_ELWA_2": return_lower_bull(vertrieb_angebot.elwa),
            "AC_THOR": return_lower_bull(vertrieb_angebot.thor),
            "AC_THOR_Heizstab": vertrieb_angebot.heizstab,
            "Smart_Dongle_LTE": vertrieb_angebot.smartDongleLte,
            "MID_Anzahl": int(vertrieb_angebot.midZaehler),
            "APZ_Feld": return_lower_bull(vertrieb_angebot.apzFeld),
            "APZ_Feld_UVV": return_lower_bull(vertrieb_angebot.apzFeldUVV),
            "Z_hlerschrank": return_lower_bull(vertrieb_angebot.zaehlerschrank),
            "Potentialausgleich": return_lower_bull(vertrieb_angebot.potentialausgleich),
            "Beta_Platte": return_lower_bull(vertrieb_angebot.beta_platte),
            "Metalldachziegel": return_lower_bull(vertrieb_angebot.metall_ziegel),
            "PREFA_Dachbefestigung": return_lower_bull(vertrieb_angebot.prefa_befestigung),
            "Ger_st_durch_Kunde": return_lower_bull(vertrieb_angebot.geruestKunde),
            "Ger_st_oeffentlich": return_lower_bull(vertrieb_angebot.geruestOeffentlich) and not return_lower_bull(vertrieb_angebot.geruestKunde),
            "Dachhaken_durch_Kunde": return_lower_bull(vertrieb_angebot.dachhakenKunde),
            "Rabatt": int(vertrieb_angebot.rabatt),
            "Individueller_Text": str(vertrieb_angebot.indiv_text),
            "Zahlungsmodalit_ten": str(vertrieb_angebot.zahlungsbedingungen),
            "Angebotssumme": str(vertrieb_angebot.angebotsumme),
            "Finanzierung": return_lower_bull(vertrieb_angebot.finanzierung),
        }
    }
    try:
        response = requests.post(url, json=dataMap, headers=headers)
        response_data = response.json()
        new_record_id = response_data["data"]["ID"]
        log_and_notify(
            f"Neue Angebot nach Zoho gesendet record ID: {new_record_id}, Angebotssumme: {vertrieb_angebot.angebotsumme}"
        )
        return response
    except:
        pass


def pushTicket(vertrieb_ticket, user_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/junosolar/juno-kleinanlagen-portal/form/Angebot"
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    date_obj_gultig = datetime.datetime.strptime(
        vertrieb_ticket.angebot_gultig, "%d.%m.%Y"
    )
    formatted_gultig_date_str = date_obj_gultig.strftime("%d-%b-%Y")

    dataMap = {
        "data": {
            "Angebot_ID": str(vertrieb_ticket.ticket_id),
            "Typ": "Ticket",
            "Privatkunde_ID": str(vertrieb_ticket.zoho_id),
            "Vertriebler_ID": str(user_zoho_id),
            "erstellt_am": str(vertrieb_ticket.anfrage_vom),
            "g_ltig_bis": formatted_gultig_date_str,
            "Anz_Speicher": str(vertrieb_ticket.anz_speicher),
            "Wallbox_Typ": str(vertrieb_ticket.wallboxtyp),
            "Wallbox_Anzahl": str(vertrieb_ticket.wallbox_anzahl),
            "SolarModule_Typ": str(vertrieb_ticket.solar_module),
            "SolarModule_Leistung": str(vertrieb_ticket.modulleistungWp),
            "SolarModule_Menge": str(vertrieb_ticket.modulanzahl),
            "Speicher_Typ": str(vertrieb_ticket.speicher_model),
            "Smartmeter_Typ":str(vertrieb_ticket.smartmeter_model),
            "Wandhalterung_Anzahl": int(
                vertrieb_ticket.anz_wandhalterung_fuer_speicher
            ),
            "Notstrom": return_lower_bull(vertrieb_ticket.notstrom),
            "Ersatzstrom": return_lower_bull(vertrieb_ticket.ersatzstrom),
            "Optimierer_Menge": str(vertrieb_ticket.anzOptimizer),
            "WR_Tausch": str(vertrieb_ticket.wr_tausch),
            "AC_ELWA_2": return_lower_bull(vertrieb_ticket.elwa),
            "AC_THOR": return_lower_bull(vertrieb_ticket.thor),
            "AC_THOR_Heizstab": vertrieb_ticket.heizstab,
            "Smart_Dongle_LTE": vertrieb_ticket.smartDongleLte,
            "MID_Anzahl": int(vertrieb_ticket.midZaehler),
            "APZ_Feld": return_lower_bull(vertrieb_ticket.apzFeld),
            "APZ_Feld_UVV": return_lower_bull(vertrieb_ticket.apzFeldUVV),
            "Z_hlerschrank": return_lower_bull(vertrieb_ticket.zaehlerschrank),
            "Potentialausgleich": return_lower_bull(vertrieb_ticket.potentialausgleich),
            "Beta_Platte": return_lower_bull(vertrieb_ticket.beta_platte),
            "Metalldachziegel": return_lower_bull(vertrieb_ticket.metall_ziegel),
            "PREFA_Dachbefestigung": return_lower_bull(vertrieb_ticket.prefa_befestigung),
            "Ger_st_durch_Kunde": return_lower_bull(vertrieb_ticket.geruestKunde),
            "Ger_st_oeffentlich": return_lower_bull(vertrieb_ticket.geruestOeffentlich) and not return_lower_bull(vertrieb_ticket.geruestKunde),
            "Dachhaken_durch_Kunde": return_lower_bull(vertrieb_ticket.dachhakenKunde),
            "Rabatt": int(vertrieb_ticket.rabatt),
            "Individueller_Text": str(vertrieb_ticket.indiv_text),
            "Angebotssumme": str(vertrieb_ticket.angebotsumme),
        }
    }
    try:
        response = requests.post(url, json=dataMap, headers=headers)
        response_data = response.json()
        new_record_id = response_data["data"]["ID"]
        log_and_notify(
            f"Neuen Nachverkauf nach Zoho gesendet record ID: {new_record_id}, Angebotssumme: {vertrieb_ticket.angebotsumme}"
        )
        return response
    except:
        pass


def delete_redundant_angebot(angebot_zoho_id):
    url = f"https://creator.zoho.eu/api/v2/junosolar/juno-kleinanlagen-portal/report/Angebote/{angebot_zoho_id}"
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.delete(url, headers=headers)
    if not response:

        pass
    else:

        pass