import os, json, requests, time, logging
from dotenv import set_key, load_dotenv
from projektant_interface.models import (
    Project,
    Elektriktermin,
    Bautermine,
    Module1,
    Wallbox1,
    Wechselrichter1,
    Speicher,
)
from random import randint
from pprint import pprint, pformat, pp
from django.contrib.auth import get_user_model
from shared.projektant_text_processing import handle_message
from config.settings import (
    ENV_FILE,
    ACCESS_TOKEN_URL,
    ZOHO_ACCESS_TOKEN,
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    DEFAULT_EMAIL_DOMAIN,
    DEFAULT_USER_CREATION_PASSWORD,
    DEFAULT_PHONE,
)

BASE_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/PVA_klein1"

User = get_user_model()

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
LIMIT = 25
MAX_RETRIES = 20
SLEEP_TIME = 1

from datetime import datetime


def convert_date_format(date_string):
    try:
        return datetime.strptime(date_string, "%d-%b-%Y").date().strftime("%Y-%m-%d")
    except ValueError:
        return None


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
        'refresh_token': ZOHO_REFRESH_TOKEN,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
    response = requests.post(ACCESS_TOKEN_URL, params=params)
    print("REFRESH TOKEN", response)
    if response.status_code != HTTP_OK:
        raise APIException(f"Error refreshing token: {response.status_code}")
    
    new_access_token = response.json().get("access_token")
    if new_access_token:
        set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_access_token)
        return new_access_token
    else:
        raise APIException("New access token not found in the API response.")
    


def fetch_records(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == HTTP_OK:
        return response.json()
    elif response.status_code == HTTP_UNAUTHORIZED:
        headers["Authorization"] = f"Zoho-oauthtoken {refresh_access_token()}"
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == HTTP_OK:
            return response.json()

    
def create_project_instances_from_zoho():
    endpoint = BASE_URL  # replace with your specific endpoint
    headers = get_headers()
    params = {"limit": LIMIT}

    data = fetch_records(endpoint, headers, params)
    new_projects_count = 0
    for record in data.get("data", []):
        exists = Project.objects.filter(ID=record["ID"]).exists()
        if not exists:
            new_projects_count += 1

            project, created = Project.objects.get_or_create(ID=record["ID"])

            project.Status = record.get("Status")
            project.Auftragsbest_tigung_versendet = record.get(
                "Auftragsbest_tigung_versendet"
            )
            date_string = record.get("Auftrag_Erteilt_am") or "08-Aug-2000"
            if date_string:
                project.Auftrag_Erteilt_am = convert_date_format(date_string)

            project.Bautermine = str(record.get("Bautermine"))
            project.Modul_Summe_kWp = record.get("Modul_Summe_kWp")
            project.Module1 = str(record.get("Module1"))
            project.Besonderheiten = record.get("Besonderheiten")
            try:
                record.get("Besonderheiten") != ""
                project.Processed_Besonderheiten == "keine Beschreibung"
                project.Processed_Besonderheiten = handle_message(
                    str(record.get("Besonderheiten"))
                )
            except:
                pass
            project.Elektriktermin = str(
                record.get("Elektriktermin")
            )  # Assuming it's a list of dictionaries
            project.Kunde_display_value = str(record.get("Kunde"))
            project.Rechnung_versandt = record.get("Rechnung_versandt")
            project.Lieferung = record.get("UK_vsl_Lieferung")
            project.Berechnung_erhalten_am = record.get("Berechnung_erhalten_am")
            project.EDDI = record.get("EDDI") == "❌"
            project.Netzbetreiber = record.get("Netzbetreiber")
            project.Garantie_WR_beantragt_am = record.get("Garantie_WR_beantragt_am")
            project.Ticket_form = str(record.get("Ticket_form"))
            project.Status_Inbetriebnahmeprotokoll = record.get(
                "Status_Inbetriebnahmeprotokoll"
            )
            project.Zahlungsmodalit_ten = record.get("Zahlungsmodalit_ten")
            project.Berechnung_bergeben_am = record.get("Berechnung_bergeben_am")
            project.Vertriebler = record.get("Vertriebler")
            project.Notstromversorgung_Backup_Box_vorhanden = (
                record.get("Notstromversorgung_Backup_Box_vorhanden") == "❌"
            )
            project.Status_Marktstammdatenregistrierung = record.get(
                "Status_Marktstammdatenregistrierung"
            )
            project.Garantieerweiterung = record.get("Garantieerweiterung")
            project.Bauabschluss_am = record.get("Bauabschluss_am")
            project.Status_Betreiberwechsel = record.get("Status_Betreiberwechsel")
            project.Status_Einspeiseanfrage = record.get("Status_Einspeiseanfrage")
            project.Wallbox1 = str(record.get("Wallbox1"))
            project.Hub1 = record.get("Hub1") == "❌"
            project.Kunde_Kundennummer = record.get("Kunde.Kundennummer")
            project.UK_auf_Lager = record.get("UK_auf_Lager") == "❌"
            project.Wechselrichter1 = str(record.get("Wechselrichter1"))
            project.UK_bestellt_am = record.get("UK_bestellt_am")
            project.Power_Boost_vorhanden = record.get("Power_Boost_vorhanden") == "❌"
            project.Unterkonstruktion1 = record.get("Unterkonstruktion1")
            project.Harvi1 = record.get("Harvi1")
            project.Optimizer1 = record.get("Optimizer1")
            project.Kunde_Adresse_PVA = record.get("Kunde.Adresse_PVA")
            project.Status_Elektrik = record.get("Status_Elektrik")
            project.Kunde_Email = record.get("Kunde.Email")
            project.Termin_Z_hlerwechsel = record.get("Termin_Z_hlerwechsel")
            project.Nummer_der_PVA = record.get("Nummer_der_PVA")
            project.Kunde_Postanschrift = record.get("Kunde.Postanschrift")
            project.Kunde_Telefon_Festnetz = record.get("Kunde.Telefon_Festnetz")
            project.Speicher = str(
                record.get("Speicher")
            )  # Assuming it's a list of dictionaries
            project.Status_Fertigmeldung = record.get("Status_Fertigmeldung")
            project.Bauleiter = record.get("Bauleiter")
            project.Hauselektrik = record.get("Hauselektrik")
            project.Kunde_Telefon_mobil = record.get("Kunde.Telefon_mobil")

            project.save()
    if new_projects_count == 0:
        return "No new records existing in ZOHO"
    else:
        return f"{new_projects_count} new projects were created from ZOHO records"


def populate_project_instance_from_zoho(project_id):
    endpoint = BASE_URL + f"/{project_id}"
    headers = get_headers()
    start_index = 1
    params = {
        "from": start_index,
        "limit": LIMIT,}

    print(project_id)
    response_data = fetch_records(endpoint, headers, params)
    print(response_data)
    # if response_data and not response_data.get("data"):
    #     return None
    if response_data is not None:
        record = response_data["data"]

        defaults = {
            "UK_vsl_Lieferung": record.get("UK_vsl_Lieferung", ""),
            "Modul_Summe_kWp": record.get("Modul_Summe_kWp", ""),
            "Berechnung_erhalten_am": record.get("Berechnung_erhalten_am", ""),
            "Module1": str(record.get("Module1", [])),
            "EDDI": record.get("EDDI") == "❌",
            "Besonderheiten": record.get("Besonderheiten", ""),
            "Netzbetreiber": record.get("Netzbetreiber", ""),
            "Garantie_WR_beantragt_am": record.get("Garantie_WR_beantragt_am", ""),
            "Ticket_form": record.get("Ticket_form", ""),
            "Status_Inbetriebnahmeprotokoll": record.get(
                "Status_Inbetriebnahmeprotokoll", ""
            ),
            "Auftragsbest_tigung_versendet": record.get(
                "Auftragsbest_tigung_versendet", ""
            ),
            "Auftrag_Erteilt_am": convert_date_format(
                record.get("Auftrag_Erteilt_am", "08-Aug-2000")
            ),
            "Zahlungsmodalit_ten": record.get("Zahlungsmodalit_ten", ""),
            "Berechnung_bergeben_am": record.get("Berechnung_bergeben_am", ""),
            "Vertriebler": record.get("Vertriebler", ""),
            "Notstromversorgung_Backup_Box_vorhanden": record.get(
                "Notstromversorgung_Backup_Box_vorhanden", ""
            )
            == "❌",
            "Status_Marktstammdatenregistrierung": record.get(
                "Status_Marktstammdatenregistrierung", ""
            ),
            "Garantieerweiterung": record.get("Garantieerweiterung", ""),
            "Bauabschluss_am": record.get("Bauabschluss_am", ""),
            "Rechnung_versandt": record.get("Rechnung_versandt", ""),
            "Status_Betreiberwechsel": record.get("Status_Betreiberwechsel", ""),
            "Status_Einspeiseanfrage": record.get("Status_Einspeiseanfrage", ""),
            "Wallbox1": str(record.get("Wallbox1", [])),
            "Hub1": record.get("Hub1", "") == "❌",
            "Status": record.get("Status", ""),
            "Lager": record.get("UK_auf_Lager", "") == "❌",
            "Wechselrichter1": str(record.get("Wechselrichter1", [])),
            "UK_bestellt_am": record.get("UK_bestellt_am", ""),
            "Power_Boost_vorhanden": record.get("Power_Boost_vorhanden", "") == "❌",
            "Unterkonstruktion1": record.get("Unterkonstruktion1", ""),
            "Harvi1": record.get("Harvi1", ""),
            "Optimizer1": record.get("Optimizer1", ""),
            "Kunde_Adresse_PVA": record.get("Kunde.Adresse_PVA", ""),
            "Status_Elektrik": record.get("Status_Elektrik", ""),
            "Kunde_Kundennummer": record.get("Kunde.Kundennummer"),
            "Kunde_display_value": record.get("Kunde", {}),
            "Kunde_Email": record.get("Kunde.Email", ""),
            "Termin_Z_hlerwechsel": record.get("Termin_Z_hlerwechsel", ""),
            "Nummer_der_PVA": record.get("Nummer_der_PVA", ""),
            "Kunde_Postanschrift": record.get("Kunde.Postanschrift", ""),
            "Kunde_Telefon_Festnetz": record.get("Kunde.Telefon_Festnetz", ""),
            "Speicher": str(record.get("Speicher", [])),
            "Status_Fertigmeldung": record.get("Status_Fertigmeldung", ""),
            "Bauleiter": record.get("Bauleiter", ""),
            "Hauselektrik": record.get("Hauselektrik", ""),
            "Kunde_Telefon_mobil": record.get("Kunde.Telefon_mobil", ""),
        }
        try:
            existing_project = Project.objects.get(ID=project_id)
        except Project.DoesNotExist:
            existing_project = None

        # If project instance exists, only update fields that are None or ""
        if existing_project:
            for field_name, new_value in defaults.items():
                current_value = getattr(existing_project, field_name, None)
                if current_value in [None, ""]:
                    setattr(existing_project, field_name, new_value)
            existing_project.save()
            project = existing_project
        else:
            # If project instance does not exist, create a new one with the defaults
            project = Project.objects.create(ID=project_id, **defaults)
            project.save()
        return project

    else:
        pass

    


def update_all_project_instances():
    # Fetch all the Project instances
    all_projects = Project.objects.all()

    # Counter for updated projects
    updated_count = 0

    # For each project, call the populate_project_instance_from_zoho function
    for project in all_projects:
        updated_project = populate_project_instance_from_zoho(project.ID)
        if updated_project:
            updated_count += 1
            print(f"Updating record...{updated_count}")
        if updated_count == 50:
            break

    return f"Updated {updated_count} out of {all_projects.count()} projects."
