from pathlib import Path
import os, sys, dj_database_url  # type:ignore
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"

# Load the .env file
load_dotenv(ENV_FILE)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
# ALLOWED_HOSTS = ["*"]
LOGIN_URL = "/login"

DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
DEVELOPMENT_MODE = os.getenv("DEVELOPEMENT_MODE", "FALSE") == "True"

# Application definition

# Application definition
PROJECT_APPS = [
    "authentication",
    "prices",
    "config",
    "invoices",
    "elektriker_kalender",
    "vertrieb_interface",
    "adminfeautures",
]


DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

SERVICE_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "widget_tweaks",
    "schema_graph",
    "crispy_forms",
    "shared",
    "storages",
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + SERVICE_APPS

SIMPLE_JWT = {
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_SERIALIZER_CLASS": "accounts.jwt_utils.CustomTokenObtainPairSerializer",
}

AUTH_USER_MODEL = "authentication.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DEFAULT_EMAIL_DOMAIN = os.getenv("DEFAULT_EMAIL_DOMAIN")
DEFAULT_USER_CREATION_PASSWORD = os.getenv("DEFAULT_USER_CREATION_PASSWORD")
DEFAULT_PHONE = os.getenv("DEFAULT_PHONE")
BASE_URL = os.getenv("BASE_URL")
BASE_URL_PRIV_KUNDEN = os.getenv("BASE_URL_PRIV_KUNDEN")
REFRESH_URL = os.getenv("REFRESH_URL")
ACCESS_TOKEN_URL = os.getenv("ACCESS_TOKEN_URL")
ZOHO_ACCESS_TOKEN = os.getenv("ZOHO_ACCESS_TOKEN")
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
SERVER_UPLINK_KEY = os.getenv("SERVER_UPLINK_KEY")
CLIENT_UPLINK_KEY = os.getenv("CLIENT_UPLINK_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", default="openaikey")

if DEVELOPMENT_MODE is True:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
elif len(sys.argv) > 0 and sys.argv[1] != "collectstatic":
    if os.getenv("DATABASE_URL", None) is None:
        raise Exception("DATABASE_URL environment variable not defined")
    DATABASES = {
        "default": dj_database_url.parse(os.environ.get("DATABASE_URL")), #type: ignore
    }
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.getenv("POSTGRES_DB", default="support_2"),
#         "USER": os.getenv("POSTGRES_USER", default="support_1"),
#         "PASSWORD": os.getenv("POSTGRES_PASSWORD", default="support1234"),
#         "HOST": os.getenv("POSTGRES_HOST", default="localhost"),
#         "PORT": int(os.getenv("POSTGRES_PORT", default="5432")),
#     }
# }
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
MEDIA_PDF_URL = "media/pdf/"

# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_STATIC_LOCATION = 'static'
# STATIC_URL = AWS_S3_ENDPOINT_URL + '/static/'
