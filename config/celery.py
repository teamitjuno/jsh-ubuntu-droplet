from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

from celery.schedules import crontab
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

username = settings.RABBITMQ_DEFAULT_USER
password = settings.RABBITMQ_DEFAULT_PASS

app = Celery("config", broker=f"amqp://{username}:{password}@rabbitmq:5672//")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

# Konfiguration der periodischen Aufgaben für Celery
app.conf.beat_schedule = {
    "delete_unassigned_vertriebangebot_week_old": {
        # Task für die Löschung nicht zugewiesener Instanzen, die alle 5 Minuten durchgeführt wird
        "task": "vertrieb_interface.tasks.delete_unassigned_vertriebangebot_week_old",
        "schedule": crontab(minute='*/5'),  # Jede 5 Minuten
    },
    "delete_vertriebangebot_six_weeks_old": {
        # Task für die Löschung aller Instanzen, die seit sechs Wochen nicht aktualisiert wurden
        "task": "vertrieb_interface.tasks.delete_vertriebangebot_six_weeks_old",
        "schedule": crontab(
            day_of_week=0, hour=1, minute=0
        ),  # Wöchentlich, Sonntags um 01:00 Uhr
    },
    "delete_angenommen_vertriebangebot_two_months_old": {
        # Task für die Löschung von 'angenommen' Instanzen, die seit zwei Monaten nicht aktualisiert wurden
        "task": "vertrieb_interface.tasks.delete_angenommen_vertriebangebot_two_months_old",
        "schedule": crontab(
            day_of_month=1, hour=2, minute=0
        ),  # Monatlich am ersten Tag des Monats um 02:00 Uhr
    },
}
app.autodiscover_tasks()