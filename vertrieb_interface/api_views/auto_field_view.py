# VertriebAutoFieldView.py
# Django related imports
from django.views.generic import View
from django.http import JsonResponse

# Python standard libraries
import json

# Local application imports
from vertrieb_interface.api_views.common import load_json_data, update_list
from vertrieb_interface.api_views.auth_checkers import VertriebCheckMixin
from vertrieb_interface.zoho_api_connector import (
    fetch_user_angebote_all,
    fetch_user_angebote_limit,
)
from authentication.models import User


class VertriebAutoFieldView(View, VertriebCheckMixin):
    """
    Eine Django-View, die eine API für das AutoVervollständigen von Vertriebsdaten bereitstellt.
    Nutzt die Zoho API, um Daten basierend auf Benutzereingaben zu holen und zu filtern.
    """

    def get(self, request, *args, **kwargs):
        """
        Behandelt GET-Anfragen für die AutoVervollständigungsfunktion.

        :param request: Das HTTP-Anfrageobjekt.
        :returns: JsonResponse Objekt mit Daten oder einer Fehlermeldung.
        """
        user = request.user

        # Daten laden oder abrufen
        data = self.load_or_fetch_data(user, request)

        # Name extrahieren und Daten bereitstellen
        name = request.GET.get("name")
        if not name:
            return JsonResponse(
                {"error": "Kein Name-Parameter bereitgestellt"}, status=400
            )

        response_data = self.find_data_by_name(data, name)
        if response_data is None:
            return JsonResponse(
                {"error": "Keine Daten für den angegebenen Namen gefunden"}, status=404
            )

        return JsonResponse(response_data, safe=False)

    def load_or_fetch_data(self, user, request):
        """
        Lädt Daten aus dem Cache des Benutzers oder holt sie von der Zoho API, wenn sie nicht vorhanden sind.

        :param user: Das Benutzerobjekt, das die Daten enthält.
        :param request: Das HTTP-Anfrageobjekt.
        :returns: Ein Datenobjekt.
        """
        try:
            data = load_json_data(user.zoho_data_text)
            
            return data
        except json.JSONDecodeError:
            return self.fetch_and_save(user, request, fetch_user_angebote_all)

    def fetch_and_save(self, user, request, fetch_method, limit=None):
        """
        Ruft Daten von der Zoho API ab und speichert sie im Benutzerobjekt.

        :param user: Das Benutzerobjekt, das die Daten speichert.
        :param request: Das HTTP-Anfrageobjekt.
        :param fetch_method: Die Methode zum Abrufen der Daten.
        :param limit: Optionaler Parameter für die Begrenzung der abgerufenen Datensätze.
        :returns: Ein Datenobjekt.
        """
        data = fetch_method(request, limit) if limit else fetch_method(request)
        user.zoho_data_text = json.dumps(data)
        user.save()
        return load_json_data(user.zoho_data_text)

    def find_data_by_name(self, data, name):
        """
        Durchsucht die Daten nach einem Eintrag mit dem spezifizierten Namen.

        :param data: Die Liste der Datenobjekte.
        :param name: Der Name, nach dem gesucht wird.
        :returns: Das gefundene Datenobjekt oder None.
        """
        return next((item for item in data if item.get("name") == name), None)
