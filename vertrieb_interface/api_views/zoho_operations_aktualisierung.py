from django.http import HttpResponse, JsonResponse
import json

# Importiere Hilfsfunktionen und Modelle aus dem vertrieb_interface Modul
from vertrieb_interface.api_views.common import load_json_data, update_list
from vertrieb_interface.models import VertriebAngebot
from vertrieb_interface.zoho_api_connector import (
    fetch_user_angebote_all,
)
from authentication.models import User


def load_user_json_data(request):
    user_data = load_json_data(request.user.zoho_data_text)
    if user_data is None:
        raise ValueError("Failed to decode JSON from user's Zoho data.")
    if not user_data:
        raise ValueError("No data found in user's Zoho data.")
    return user_data


def delete_unexisting_records(request):
    """
    Entfernt Datensätze, die nicht mehr in Zoho vorhanden sind, aus der VertriebAngebot Datenbank.

    Args:
    request: Django HttpRequest-Objekt, das Daten des Benutzers enthält.

    Returns:
    HttpResponse: Gibt den Status der Operation zurück, einschließlich der Anzahl der aktualisierten Datensätze.
    """
    try:
        # Lade Benutzerdaten aus der Anfrage
        user_data = load_user_json_data(request)
        user_zoho_ids = {item.get("zoho_id") for item in user_data}
        print(user_zoho_ids)

        # Filtere Angebote, die aktualisiert werden müssen
        vertrieb_angebots_to_update = VertriebAngebot.objects.filter(
            user=request.user, angebot_id_assigned=True
        ).exclude(zoho_id__in=user_zoho_ids)

        # Aktualisiere die gefilterten Angebote
        updated_count = vertrieb_angebots_to_update.update(angebot_id_assigned=False)
        return HttpResponse(f"Updated {updated_count} records.", status=200)
    except ValueError as e:
        return HttpResponse(str(e), status=400)


def update_status_to_angenommen(request):
    """
    Aktualisiert den Status von Angeboten auf 'angenommen', basierend auf den Daten von Zoho.

    Args:
    request: Django HttpRequest-Objekt, das Daten des Benutzers enthält.

    Returns:
    HttpResponse: Gibt den Erfolg oder Fehler der Operation zurück.
    """
    try:
        user_data = load_user_json_data(request)
        zoho_id_to_attributes = {
            item["zoho_id"]: {
                "name": item["name"],
                "name_first_name": item["name_first_name"],
                "name_last_name": item["name_last_name"],
                "name_suffix": item["name_suffix"],
                "status": item["status"],
                "status_pva": item["status_pva"],
                "angenommenes_angebot": item["angenommenes_angebot"],
            }
            for item in user_data
        }

        vertrieb_angebots_to_update = VertriebAngebot.objects.filter(
            user=request.user,
            angebot_id_assigned=True,
        )

        updates = []
        for angebot in vertrieb_angebots_to_update:
            attrs = zoho_id_to_attributes.get(angebot.zoho_id)
            if attrs:
                angebot.name = attrs["name"]
                angebot.name_first_name = attrs["name_first_name"]
                angebot.name_last_name = attrs["name_last_name"]
                angebot.name_suffix = attrs["name_suffix"]
                angebot.status = attrs["status"]
                angebot.status_pva = attrs["status_pva"]
                angebot.angenommenes_angebot = attrs["angenommenes_angebot"]
                updates.append(angebot)

        # Führe eine Massenaktualisierung der relevanten Felder durch
        VertriebAngebot.objects.bulk_update(
            updates,
            [
                "name",
                "name_first_name",
                "name_last_name",
                "name_suffix",
                "status",
                "status_pva",
                "angenommenes_angebot",
            ],
        )
        return HttpResponse("Updated statuses successfully.", status=200)
    except ValueError as e:
        return HttpResponse(str(e), status=400)


def load_user_angebots(request):
    """
    Lädt Angebote für den Benutzer und führt erforderliche Aktualisierungen durch.

    Args:
    request: Django HttpRequest-Objekt, das Daten des Benutzers enthält.

    Returns:
    JsonResponse: Gibt das Ergebnis der Operation zurück, einschließlich Fehler- oder Erfolgsstatus.
    """
    try:
        all_user_angebots_list = fetch_user_angebote_all(request)
        request.user.zoho_data_text = json.dumps(all_user_angebots_list)
        request.user.save()
    except Exception:
        all_user_angebots_list = fetch_user_angebote_all(request)
        request.user.zoho_data_text = json.dumps(all_user_angebots_list)
        request.user.save()

    # Bearbeite Antworten von Hilfsfunktionen
    response1 = delete_unexisting_records(request)
    response2 = update_status_to_angenommen(request)

    # Überprüfe die Antwortcodes und gebe entsprechend das Ergebnis zurück
    if response1.status_code != 200 or response2.status_code != 200:
        return JsonResponse({"status": "error"}, status=500)

    return JsonResponse({"status": "success"}, status=200)

def changeVerguetung(bis10, bis40):
    """
        Überschreibt den Startwert der Einspeisevergütungen für jeden Nutzer.

        Args:
        bis10: Int, der als Centwert für die Vergütung bis 10 kWp gesetzt werden soll
        bis40: Int, der als Centwert für die Vergütung bis 40 kWp gesetzt werden soll

        Returns:
        None
        """
    if bis10 is not None and bis40 is not None:
        users = User.objects.all()
        for user in users:
            User.objects.filter(zoho_id=user.zoho_id).update(initial_bis10kWp=bis10)
            User.objects.filter(zoho_id=user.zoho_id).update(initial_bis40kWp=bis40)

def changeKabel(initial):
    """
        Überschreibt den Startwert der Kabelanschlusslänge für jeden Nutzer.

        Args:
        initial: Int, der als initiale Kabelanschlusslänge gesetzt werden soll

        Returns:
        None
        """
    if initial is not None:
        users = User.objects.all()
        for user in users:
            User.objects.filter(zoho_id=user.zoho_id).update(initial_kabelanschluss=initial)

def activateAccount(email):
    """
        Aktiviert einen Nutzeraccount anhand der Mail-Adresse.

        Args:
        email: String, der Mail-Adresse des Nutzers enthält

        Returns:
        None
        """
    if email is not None:
        User.objects.filter(email=email).update(is_active=True)