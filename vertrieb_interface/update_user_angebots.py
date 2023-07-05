import os, requests, json
from dotenv import set_key, load_dotenv
from config.settings import ENV_FILE

# Global constants


URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"

load_dotenv(ENV_FILE)

BASE_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Elektrikkalender"
ACCESS_TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
LIMIT = 100
MAX_RETRIES = 5
SLEEP_TIME = 1


class APIException(Exception):
    pass


class UnauthorizedException(APIException):
    pass


class RateLimitExceededException(APIException):
    pass


def create_angebot_pdf_user(vertriebler_id):
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        access_token = refresh_access_token()

    url = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    # Define an empty set to store unique Vertriebler data
    vertriebler_set = set()

    # Specify the number of records to fetch per request
    limit = 200
    start_index = 0

    while True:
        params = {
            "from": start_index,
            "limit": limit,
            "criteria": f"Vertriebler.ID == {vertriebler_id}",
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 401:
            access_token = refresh_access_token()
            headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
            continue

        # Check the response status code
        elif response.status_code != 200:
            print(f"Failed to fetch data, status code: {response.status_code}")
            break
        print(f"access_token is alive, status code: {response.status_code}")
        data = json.loads(response.text)

        if not data["data"]:
            break

        for record in data["data"]:
            if (
                "Vertriebler" in record
                and "display_value" in record["Vertriebler"]
                and "ID" in record["Vertriebler"]
            ):
                vertriebler_set.add(
                    (
                        record["Vertriebler"]["display_value"],
                        record["Vertriebler"]["ID"],
                    )
                )

        # Update the start index for the next batch of records
        start_index += limit

    # Convert the set to a list and print
    vertriebler_list = list(vertriebler_set)
    vertriebler_list = json.dumps(vertriebler_list, indent=4)
    with open("vertrieb_angebots_list.json", "w") as f:
        json.dump(vertriebler_list, f)
    return vertriebler_list


def process_all_user_data(data, all_user_angebots_list):
    if not data["data"]:
        return all_user_angebots_list

    for item in data["data"]:
        if "ID" in item:
            all_user_angebots_list.append(
                {
                    "zoho_id": item.get("ID", ""),
                    "status": item.get("Status", ""),
                    "anrede": item.get("Name", {}).get("prefix", ""),
                    "strasse": item.get("Adresse_PVA", {}).get("address_line_1", ""),
                    "ort": item.get("Adresse_PVA", {}).get("postal_code", "")
                    + " "
                    + item.get("Adresse_PVA", {}).get("district_city", ""),
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
                    "name": item.get("Name", {}).get("first_name", "")
                    + " "
                    + item.get("Name", {}).get("suffix", "")
                    + " "
                    + item.get("Name", {}).get("last_name", ""),
                    "vertriebler_display_value": item.get("Vertriebler", {}).get(
                        "display_value", ""
                    ),
                    "vertriebler_id": item.get("Vertriebler", {}).get("ID", ""),
                    "adresse_pva_display_value": item.get("Adresse_PVA", {}).get(
                        "display_value", ""
                    ),
                    "anfrage_vom": item.get("Anfrage_vom", ""),
                }
            )
    return all_user_angebots_list


def refresh_access_token():
    client_id = os.getenv("ZOHO_CLIENT_ID")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET")
    refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")

    url = f"https://accounts.zoho.eu/oauth/v2/token?refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token"

    response = requests.post(url)

    if response.status_code == 200:
        data = response.json()
        new_access_token = data.get("access_token")
        print("Access token refreshed.", new_access_token)
        set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_access_token)
        load_dotenv(ENV_FILE)

        return new_access_token
    else:
        print(f"Error refreshing token: {response.status_code}")
