from vertrieb_interface.api_views.common import load_json_data

import json


from django.http import (
    HttpResponse,
    JsonResponse,
)


from vertrieb_interface.zoho_api_connector import (
    fetch_user_angebote_all,
)
from vertrieb_interface.models import VertriebAngebot

def delete_unexisting_records(request):
    user = request.user
    user_data = load_json_data(user.zoho_data_text)
    
    if user_data is None:
        return HttpResponse("Failed to decode JSON from user's Zoho data.", status=400)
    if not user_data:
        return HttpResponse("No data found in user's Zoho data.", status=200)

    user_zoho_ids = {item.get("zoho_id") for item in user_data}

    vertrieb_angebots_to_update = VertriebAngebot.objects.filter(
        user=user, angebot_id_assigned=True
    ).exclude(
        zoho_id__in=user_zoho_ids
    )

    updated_count = vertrieb_angebots_to_update.update(angebot_id_assigned=False)
    return HttpResponse(f"Updated {updated_count} records.", status=200)


def update_status_to_angenommen(request):
    user = request.user
    user_data = load_json_data(user.zoho_data_text)
    
    if user_data is None:
        return HttpResponse("Failed to decode JSON from user's Zoho data.", status=400)

    
    zoho_id_to_attributes = {
        item["zoho_id"]: {
            "status": item["status"],
            "status_pva": item["status_pva"],
            "angenommenes_angebot": item["angenommenes_angebot"]
        } for item in user_data
    }

    vertrieb_angebots_to_update = VertriebAngebot.objects.filter(
        user=user, angebot_id_assigned=True, zoho_id__in=zoho_id_to_attributes.keys()
    )

    
    updates = []
    for angebot in vertrieb_angebots_to_update:
        attrs = zoho_id_to_attributes.get(angebot.zoho_id)
        if attrs:
            angebot.status = attrs["status"]
            angebot.status_pva = attrs["status_pva"]
            angebot.angenommenes_angebot = attrs["angenommenes_angebot"]
            updates.append(angebot)
    
    VertriebAngebot.objects.bulk_update(updates, ["status", "status_pva", "angenommenes_angebot"])
    return HttpResponse("Updated statuses successfully.", status=200)

def load_user_angebots(request):
    user = request.user
    all_user_angebots_list = fetch_user_angebote_all(request)
    user.zoho_data_text = json.dumps(all_user_angebots_list)
    user.save()

    response1 = delete_unexisting_records(request)
    response2 = update_status_to_angenommen(request)
    
    if response1.status_code != 200 or response2.status_code != 200:
        return JsonResponse({"status": "error"}, status=500)

    return JsonResponse({"status": "success"}, status=200)