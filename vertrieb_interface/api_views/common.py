# common.py
import json
from django.http import HttpResponse


def load_json_data(text):
    try:
        return json.loads(text) if text else []
    except json.JSONDecodeError:
        return []

def update_list(list1, list2):
   
    lookup_dict = {item['zoho_id']: item for item in list2}

   
    existing_ids = {item['zoho_id'] for item in list1}

    
    for i, item in enumerate(list1):
        if item['zoho_id'] in lookup_dict:
           
            list1[i] = lookup_dict[item['zoho_id']]

    
    for item in list2:
        if item['zoho_id'] not in existing_ids:
            list1.append(item)

    return list1