# common.py
import json
from django.http import HttpResponse


def load_json_data(text):
    try:
        return json.loads(text) if text else []
    except json.JSONDecodeError:
        return []


# def update_list(list1, list2):
#     """
#     Replaces dictionaries in list1 with those from list2 based on matching 'zoho_id'.
#     If no matching 'zoho_id' is found in list2, the dictionary in list1 is left unchanged.

#     :param list1: List of dictionaries, each containing details about an entry.
#     :param list2: List of dictionaries, each containing potentially new details.
#     :return: The modified version of list1 where matching dictionaries are replaced.
#     """
#     # Create a lookup dictionary from list2 using 'zoho_id' as the key
#     lookup_dict = {item['zoho_id']: item for item in list2}

#     # Iterate through list1 and replace matching entries with those from lookup_dict
#     for i, item in enumerate(list1):
#         if item['zoho_id'] in lookup_dict:
#             list1[i] = lookup_dict[item['zoho_id']]
    
#     return list1


def update_list(base_list, updates_list):
    """
    Updates the entries in base_list with the information from updates_list based on matching 'zoho_id'.
    The length of base_list remains unchanged.

    :param base_list: List of dictionaries, each containing details about an entry.
    :param updates_list: List of dictionaries, each containing updated details.
    :return: The updated version of base_list.
    """
    # Convert updates_list into a dictionary for quick access using 'zoho_id' as keys
    updates_dict = {item['zoho_id']: item for item in updates_list}

    # Iterate through each item in the base_list and update it if there's a matching 'zoho_id' in updates_dict
    for item in base_list:
        if item['zoho_id'] in updates_dict:
            # Update only the existing keys to prevent adding new fields from updates_list
            for key in item.keys():
                if key in updates_dict[item['zoho_id']]:
                    item[key] = updates_dict[item['zoho_id']][key]
    
    return base_list