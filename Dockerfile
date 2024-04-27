# Verwenden des Python 3.11 Basisbildes
FROM python:3.11

# Verhindern, dass Python pyc-Dateien schreibt
ENV PYTHONDONTWRITEBYTECODE 1
# Setzen von Python Ausgabe auf ungebüffert, d.h. sie wird sofort auf der Konsole ausgegeben
ENV PYTHONUNBUFFERED 1
# Festlegen des Django Einstellungsmoduls
ENV DJANGO_SETTINGS_MODULE=config.settings

# Festlegen des Arbeitsverzeichnisses im Container
WORKDIR /app

# Installieren der Abhängigkeiten
COPY Pipfile Pipfile.lock /app/
# Aktualisieren von pip
RUN pip install --upgrade pip
# Installieren von pipenv und Installieren der Abhängigkeiten im Systemkontext
RUN pip install pipenv && pipenv install --system

# Installieren von Supervisord zur Prozessverwaltung
RUN pip install supervisor

# Kopieren der Projektdateien in das Arbeitsverzeichnis
COPY . /app/

# Kopieren der Supervisord-Konfigurationsdatei
COPY supervisord.conf /etc/supervisord.conf

# Freigeben des Ports, auf dem die App läuft
EXPOSE 8000

# Festlegen von Supervisord als Startpunkt
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
