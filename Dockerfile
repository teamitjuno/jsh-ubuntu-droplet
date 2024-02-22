FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

COPY Pipfile Pipfile.lock /app/
RUN pip install --upgrade pip
RUN pip install pipenv && pipenv install --system

# Copying your media files
COPY ./media /app/media

COPY . /app/


# Use daphne or asgiref to run the application
CMD ["daphne", "config.asgi:application", "-b", "0.0.0.0", "-p", "8000"]