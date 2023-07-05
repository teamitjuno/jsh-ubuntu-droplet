from django.core.management.base import BaseCommand
from authentication.fetch_elektrikers import (
    APIException,
    fetch_all_elektrik_angebots,
    extract_ids,
    fetch_all_detailed_elektrik_records,
    extract_unique_elektrikers,
    convert_dict_to_list,
    create_user,
)
from dotenv import load_dotenv
import os
from config.settings import ENV_FILE

load_dotenv(ENV_FILE)


class Command(BaseCommand):
    help = "Update Elektrikers from Zoho"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting elektrikers update...")
        try:
            data = fetch_all_elektrik_angebots()
            ids = extract_ids(data)
            self.stdout.write(f"Extracted elektrikers id's : {ids}")
            self.stdout.write(f"Fetching elektrikers records ...")
            fetched_records = fetch_all_detailed_elektrik_records(ids)
            self.stdout.write(f"Records elektrikers fetched ...")
            elektrik_dict = extract_unique_elektrikers(fetched_records)
            result = convert_dict_to_list(elektrik_dict)
            self.stdout.write(f"Done... saving to database ...")

            for user_info in result:
                create_user(user_info)

            self.stdout.write(
                self.style.SUCCESS("Elektrikers update completed successfully")
            )

        except APIException as e:
            print(f"An error occurred when trying to create user: {str(e)}")
            self.stdout.write(self.style.ERROR(str(e)))
