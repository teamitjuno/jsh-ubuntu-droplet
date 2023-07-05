from django.core.management.base import BaseCommand
from authentication.fetch_elektrikers import (
    fetch_all_elektrik_angebots,
    extract_ids,
    fetch_all_detailed_elektrik_records,
)


class Command(BaseCommand):
    help = "Update Elektrikers from Zoho"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting elektrikers update...")
        try:
            data = fetch_all_elektrik_angebots()
            ids = extract_ids(data)
            fetched_records = fetch_all_detailed_elektrik_records(ids)

            for user_info in fetched_records:
                # print(user_info)
                pass
            self.stdout.write(self.style.SUCCESS(f"ElektrikerKalender : ...."))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR("An error occurred while updating elektrikers:")
            )
            self.stdout.write(self.style.ERROR(str(e)))
