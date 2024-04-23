from celery import Celery
from celery.schedules import crontab

app = Celery("Auto_Löschung")

# Konfiguration der periodischen Aufgaben für Celery
app.conf.beat_schedule = {
    "delete_unassigned_vertriebangebot_week_old": {
        # Task für die Löschung nicht zugewiesener Instanzen, die seit einer Woche nicht aktualisiert wurden
        "task": "vertrieb_interface.tasks.delete_unassigned_vertriebangebot_week_old",
        "schedule": crontab(hour=0, minute=0),  # Täglich um Mitternacht
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
