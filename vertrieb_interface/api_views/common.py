# common.py
import json
from django.http import HttpResponse


def load_json_data(text):
    try:
        return json.loads(text) if text else []
    except json.JSONDecodeError:
        return []

# def update_list(list1, list2):
   
#     lookup_dict = {item['zoho_id']: item for item in list2}

   
#     existing_ids = {item['zoho_id'] for item in list1}

    
#     for i, item in enumerate(list1):
#         if item['zoho_id'] in lookup_dict:
           
#             list1[i] = lookup_dict[item['zoho_id']]

def update_list(list1, list2):
    # Create a dictionary for quick lookup with `zoho_id` as the key
    lookup_dict = {item['zoho_id']: item for item in list2}

    # Track existing zoho_ids to identify new entries to add later
    existing_ids = {item['zoho_id'] for item in list1}

    # Update items in list1 or add new ones from list2
    for i, item in enumerate(list1):
        if item['zoho_id'] in lookup_dict:
            # Update existing dictionary with the new one from list2
            list1[i] = lookup_dict[item['zoho_id']]

    # Add items from list2 that aren't in list1
    for item in list2:
        if item['zoho_id'] not in existing_ids:
            list1.append(existing_ids[item['zoho_id']])

    return list1


