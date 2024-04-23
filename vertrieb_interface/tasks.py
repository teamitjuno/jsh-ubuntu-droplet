from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.db import transaction, DatabaseError
from vertrieb_interface.models import VertriebAngebot
import logging

# Konfigurieren des Loggers für die Ausgabe von Log-Meldungen
logger = logging.getLogger(__name__)


@shared_task
def delete_unassigned_vertriebangebot_week_old():
    """
    Löscht VertriebAngebot-Instanzen, die keine zugewiesene Angebot_ID haben und seit mindestens einer Woche nicht aktualisiert wurden.
    """
    try:
        one_week_ago = timezone.now() - timedelta(weeks=1)
        with transaction.atomic():
            to_delete = VertriebAngebot.objects.filter(
                angebot_id_assigned=False,
                updated_at__lte=one_week_ago
            )
            count = to_delete.count()
            to_delete.delete()
            logger.info(f"Deleted {count} unassigned VertriebAngebot instances not updated for over a week.")
    except DatabaseError as e:
        logger.error(f"Failed to delete VertriebAngebot instances due to a database error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

@shared_task
def delete_vertriebangebot_six_weeks_old():
    """
    Löscht alle VertriebAngebot-Instanzen, die seit mindestens sechs Wochen nicht aktualisiert wurden.
    """
    try:
        six_weeks_ago = timezone.now() - timedelta(weeks=6)
        with transaction.atomic():
            to_delete = VertriebAngebot.objects.filter(
                updated_at__lte=six_weeks_ago
            )
            count = to_delete.count()
            to_delete.delete()
            logger.info(f"Deleted {count} VertriebAngebot instances not updated for over six weeks.")
    except DatabaseError as e:
        logger.error(f"Failed to delete VertriebAngebot instances due to a database error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

@shared_task
def delete_angenommen_vertriebangebot_two_months_old():
    """
    Löscht VertriebAngebot-Instanzen mit dem Status 'angenommen', die keine zugewiesene Angebot_ID haben und seit mindestens zwei Monaten nicht aktualisiert wurden.
    """
    try:
        two_months_ago = timezone.now() - timedelta(weeks=8)
        with transaction.atomic():
            to_delete = VertriebAngebot.objects.filter(
                status='angenommen',
                angebot_id_assigned=False,
                updated_at__lte=two_months_ago
            )
            count = to_delete.count()
            to_delete.delete()
            logger.info(f"Deleted {count} 'angenommen' VertriebAngebot instances unassigned and not updated for over two months.")
    except DatabaseError as e:
        logger.error(f"Failed to delete VertriebAngebot instances due to a database error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")