FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Installing dependencies
COPY Pipfile Pipfile.lock /app/
RUN pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --system --deploy

# Install supervisord
RUN pip install supervisor

# Copy the project files
COPY . /app/

# Copy the supervisord configuration file
COPY supervisord.conf /etc/supervisord.conf

# Expose the port the app runs on
EXPOSE 8000

# Set supervisord as the entry point
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
