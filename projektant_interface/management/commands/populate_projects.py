from django.core.management.base import BaseCommand
from projektant_interface.utils import create_project_instances_from_zoho


class Command(BaseCommand):
    help = "Fetches data from ZOHO API and populates the Project model"

    def handle(self, *args, **kwargs):
        records_processed = create_project_instances_from_zoho()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {records_processed} records from ZOHO API"
            )
        )
