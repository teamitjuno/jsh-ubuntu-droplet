import json
from django.http import HttpResponse


def load_json_data(text):
    """
    Versucht, JSON-Daten aus einem gegebenen Text zu laden.

    :param text: Der Text, der JSON-Daten enthalten könnte.
    :return: Ein Python-Objekt, das aus dem JSON-Text geladen wird, oder eine leere Liste, wenn der Text leer ist oder ein Fehler auftritt.
    """
    try:
        return json.loads(text) if text else []
    except json.JSONDecodeError:
        # Rückgabe einer leeren Liste, wenn ein Fehler beim Parsen des JSON auftritt
        return []


def update_list(list1, list2):
    """
    Aktualisiert `list1` basierend auf `list2`, wobei 'zoho_id' als Schlüssel zum Auffinden und Aktualisieren von Elementen verwendet wird.

    :param list1: Die primäre Liste, die aktualisiert wird.
    :param list2: Die Liste mit neuen oder zu aktualisierenden Daten.
    :return: Eine aktualisierte Liste, die die kombinierten und aktualisierten Daten enthält.
    """
    # Erstelle ein Wörterbuch für die schnelle Suche, wobei 'zoho_id' als Schlüssel dient
    lookup_dict = {item["zoho_id"]: item for item in list2}

    # Verfolge vorhandene zoho_ids, um später neue Einträge zu identifizieren
    existing_ids = {item["zoho_id"] for item in list1}

    # Aktualisiere Elemente in list1 oder füge neue aus list2 hinzu
    for i, item in enumerate(list1):
        if item["zoho_id"] in lookup_dict:
            # Aktualisiere das vorhandene Wörterbuch mit dem neuen aus list2
            list1[i] = lookup_dict[item["zoho_id"]]

    # Füge Elemente aus list2 hinzu, die nicht in list1 sind
    for item in list2:
        if item["zoho_id"] not in existing_ids:
            list1.append(item)

    return list1
