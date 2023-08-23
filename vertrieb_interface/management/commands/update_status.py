from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from vertrieb_interface.models import VertriebAngebot


class Command(BaseCommand):
    help = "Updates the status of VertriebAngebot objects"

    def handle(self, *args, **options):
        for angebot in VertriebAngebot.objects.filter(status="bekommen"):
            if angebot.status_change_field:
                if (timezone.now().date() - angebot.status_change_field).days >= 14:
                    angebot.status = "abgelehnt"
                    angebot.save()
