import requests
import json
from dotenv import load_dotenv, set_key
from config.settings import (
    BASE_URL_PRIV_KUNDEN,
    ZOHO_ACCESS_TOKEN,
    ENV_FILE,
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
)

load_dotenv(ENV_FILE)


def fetch_vertriebler_list_IDs():
    access_token = ZOHO_ACCESS_TOKEN
    if not access_token:
        access_token = refresh_access_token()

    url = BASE_URL_PRIV_KUNDEN

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    # Define an empty set to store unique Vertriebler data
    vertriebler_set = set()

    # Specify the number of records to fetch per request
    limit = 100
    start_index = 0

    while True:
        params = {
            "from": start_index,
            "limit": limit,
        }
        response = requests.get(url, headers=headers, params=params)  # type: ignore
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
    return vertriebler_list


def refresh_access_token():
    client_id = ZOHO_CLIENT_ID
    client_secret = ZOHO_CLIENT_SECRET
    refresh_token = ZOHO_REFRESH_TOKEN

    url = f"https://accounts.zoho.eu/oauth/v2/token?refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token"

    response = requests.post(url)

    if response.status_code == 200:
        data = response.json()
        new_access_token = data.get("access_token")
        print("Access token refreshed.", new_access_token)

        set_key(ENV_FILE, "ZOHO_ACCESS_TOKEN", new_access_token)

        return new_access_token
    else:
        print(f"Error refreshing token: {response.status_code}")
