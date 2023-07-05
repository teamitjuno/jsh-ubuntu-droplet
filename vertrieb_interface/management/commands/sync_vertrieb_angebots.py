# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.contrib.auth import get_user_model

# from vertrieb_interface.models import VertriebAngebot
# import os
# from dotenv import load_dotenv, get_key, find_dotenv, set_key
# import requests
# import json

# load_dotenv()
# User = get_user_model()


# class Command(BaseCommand):
#     help = "Fetch data from Zoho API and save it to the database"

#     def add_arguments(self, parser):
#         parser.add_argument("zoho_id", type=int, help="Zoho ID of the user")

#     def fetch_all_user_angebots(self, *args, **options):
#         vertriebler_id = options["zoho_id"]
#         access_token = os.getenv("ZOHO_ACCESS_TOKEN")
#         if not access_token:
#             access_token = self.refresh_access_token()

#         url = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"

#         headers = {
#             "Authorization": f"Zoho-oauthtoken {access_token}",
#         }

#         # Define an empty set to store unique Vertriebler data
#         all_user_angebots_set = set()

#         # Specify the number of records to fetch per request
#         limit = 10
#         start_index = 1

#         while True:
#             params = {
#                 "from": start_index,
#                 "limit": limit,
#                 "criteria": f"Vertriebler.ID == {vertriebler_id}",
#             }

#             response = requests.get(url, headers=headers, params=params)
#             if response.status_code == 401:
#                 access_token = self.refresh_access_token()
#                 headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
#                 continue

#             # Check the response status code
#             elif response.status_code != 200:
#                 print(f"Failed to fetch data, status code: {response.status_code}")
#                 break
#             print(f"access_token is alive, status code: {response.status_code}")
#             data = json.loads(response.text)

#             if not data["data"]:
#                 break

#             for item in data["data"]:
#                 if "ID" in item:
#                     all_user_angebots_set.add(
#                         (
#                             item["ID"],
#                             item["Status"],
#                             item["Telefon_Festnetz"],
#                             item["Telefon_mobil"],
#                             item["PVA_klein"],
#                             item["Kundennummer"],
#                             item["Email"],
#                             item["Name"],
#                             item["Vertriebler"],
#                             item["Adresse_PVA"],
#                             item["Anfrage_vom"],
#                             item["Termine"],
#                         )
#                     )

#             start_index += limit

#         all_user_angebots_list = list(all_user_angebots_set)
#         all_user_angebots_list = json.dumps(all_user_angebots_list, indent=4)
#         print(all_user_angebots_list)
#         return all_user_angebots_list

#     def refresh_access_token(self):
#         client_id = os.getenv("ZOHO_CLIENT_ID")
#         client_secret = os.getenv("ZOHO_CLIENT_SECRET")
#         refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
#         url = f"https://accounts.zoho.eu/oauth/v2/token?refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token"
#         response = requests.post(url)
#         if response.status_code == 200:
#             data = response.json()
#             new_access_token = data.get("access_token")
#             self.stdout.write(self.style.SUCCESS("Access token refreshed."))
#             env_file = find_dotenv()
#             set_key(env_file, "ZOHO_ACCESS_TOKEN", new_access_token)
#             return new_access_token
#         else:
#             self.stdout.write(
#                 self.style.ERROR(f"Error refreshing token: {response.status_code}")
#             )

#     def update_vertrieb_angebots(self, data):
#         for item in data["data"]:
#             if isinstance(item, dict) and "ID" in item:  # this line added
#                 vertrieb_angebot, created = VertriebAngebot.objects.update_or_create(
#                     zoho_id=int(item["ID"]),
#                     defaults={
#                         "status": item.get("Status", ""),
#                         "angebot_bekommen_am": parse_date(
#                             item.get("Angebot_bekommen_am", "")
#                         ),
#                         "dachausrichtung": item.get("Dachausrichtung", ""),
#                         "email": item.get("Email", ""),
#                         "stromverbrauch_pro_jahr": item.get(
#                             "Stromverbrauch_pro_Jahr", ""
#                         ),
#                         "postanschrift": item.get("Postanschrift", ""),
#                         "notizen": item.get("Notizen", ""),
#                         "pva_klein": item.get("PVA_klein", ""),
#                         "b2b_partner": item.get("B2B_Partner", ""),
#                         "telefon_festnetz": item.get("Telefon_Festnetz", ""),
#                         "telefon_mobil": item.get("Telefon_mobil", ""),
#                         "leadstatus": item.get("Leadstatus", ""),
#                         "anfrage_ber": item.get("Anfrage_ber", ""),
#                         "empfohlen_von": item.get("empfohlen_von", ""),
#                         "adresse_pva": item.get("Adresse_PVA", ""),
#                         "anfrage_vom": parse_date(item.get("Anfrage_vom", "")),
#                         "termine_text": item.get("Termine", [{}])[0].get(
#                             "display_value", ""
#                         )
#                         if item.get("Termine")
#                         else "",
#                         "termine_id": item.get("Termine", [{}])[0].get("ID", "")
#                         if item.get("Termine")
#                         else "",
#                     },
#                 )
#             if created:
#                 self.stdout.write(
#                     self.style.SUCCESS(f"Created new VertriebAngebot: {angebot.id}")
#                 )
#             else:
#                 self.stdout.write(
#                     self.style.SUCCESS(f"Updated VertriebAngebot: {angebot.id}")
#                 )

#     def handle(self, *args, **options):
#         self.stdout.write("Fetching VertriebAngebot data from Zoho...")
#         all_user_angebots_list = self.fetch_all_user_angebots(*args, **options)

#         self.stdout.write("Updating database...")
#         for item in all_user_angebots_list:
#             item_dict = {
#                 "zoho_id": item[0],
#                 "status": item[1],
#                 "telefon_festnetz": item[2],
#                 "telefon_mobil": item[3],
#                 "pva_klein": item[4],
#                 "kundennummer": item[5],
#                 "email": item[6],
#                 "name": item[7],
#                 "vertriebler": item[8],
#                 "adresse_pva": item[9],
#                 "anfrage_vom": item[10],
#                 "termine": item[11],
#             }

#             # Update or create the VertriebAngebot
#             obj, created = VertriebAngebot.objects.update_or_create(
#                 zoho_id=item_dict["zoho_id"],
#                 defaults=item_dict,
#             )

#             if created:
#                 self.stdout.write(
#                     self.style.SUCCESS(f"Created VertriebAngebot {obj.zoho_id}")
#                 )
#             else:
#                 self.stdout.write(
#                     self.style.SUCCESS(f"Updated VertriebAngebot {obj.zoho_id}")
#                 )

#         self.stdout.write(self.style.SUCCESS("Done."))
