from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.db import transaction, DatabaseError
from .models import VertriebAngebot
import logging

# Konfigurieren des Loggers für die Ausgabe von Log-Meldungen
logger = logging.getLogger(__name__)


@shared_task
def delete_unassigned_vertriebangebot():
    """
    Löscht alle VertriebAngebot-Instanzen, bei denen angebot_id_assigned False ist und die
    seit mindestens einer Woche nicht aktualisiert wurden.
    Diese Aufgabe wird periodisch ausgeführt, um die Datenbank von nicht zugeordneten Angeboten zu bereinigen.
    """
    try:
        # Berechnung des Zeitpunkts, der genau eine Woche vor dem aktuellen Zeitpunkt liegt
        one_week_ago = timezone.now() - timedelta(days=7)

        # Start einer atomaren Datenbanktransaktion
        with transaction.atomic():
            # Abfrage aller VertriebAngebot-Instanzen, die die Kriterien erfüllen
            old_unassigned_vertriebangebots = VertriebAngebot.objects.filter(
                angebot_id_assigned=False, updated_at__lte=one_week_ago
            )

            # Zählen der betroffenen Instanzen für die Protokollierung
            count = old_unassigned_vertriebangebots.count()

            # Löschen der gefundenen Instanzen
            old_unassigned_vertriebangebots.delete()

            # Protokollierung der gelöschten Instanzen
            logger.info(
                f"Deleted {count} VertriebAngebot instances that were unassigned and not updated for over a week."
            )

    except DatabaseError as e:
        # Protokollierung eines Datenbankfehlers während der Transaktion
        logger.error(
            f"Failed to delete VertriebAngebot instances due to a database error: {e}"
        )
    except Exception as e:
        # Protokollierung anderer unerwarteter Fehler
        logger.error(f"An unexpected error occurred: {e}")
