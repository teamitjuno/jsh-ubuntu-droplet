from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"

# Load the .env file
load_dotenv(ENV_FILE)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())

# ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
ALLOWED_HOSTS = [
    "jsh-home.app",
    "www.jsh-home.app",
    "46.101.104.229",
    "138.68.100.101",
    "127.0.0.1",
    "localhost",
    "159.89.22.211",
    "http://159.89.22.211",
]
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
    "projektant_interface",
    "calculator",
    "datenblatter",
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
    # 'debug_toolbar',
    "rest_framework.authtoken",
    "widget_tweaks",
    "schema_graph",
    "crispy_forms",
    "shared",
    # "djoser",
    "storages",
    "channels",
    "corsheaders",
    "templatetags.custom_filters",
    "vertrieb_interface.templatetags.custom_filter",
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + SERVICE_APPS

SIMPLE_JWT = {
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_SERIALIZER_CLASS": "accounts.jwt_utils.CustomTokenObtainPairSerializer",
}

# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework.authentication.TokenAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
# }
# DJOSER = {
#     'LOGIN_FIELD': 'email', 
# }


AUTH_USER_MODEL = "authentication.User"

CORS_ALLOWED_ORIGINS = [
    "http://192.168.80.1",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "https://jsh-home.app",
    "https://www.jsh-home.app",
    "https://138.68.100.101",
]
CSRF_TRUSTED_ORIGINS = [
    "http://192.168.80.1",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "https://jsh-home.app",
    "https://www.jsh-home.app",
    "https://138.68.100.101",
]
CORS_ALLOW_ALL_ORIGINS = True

CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "http://159.89.22.211:80")
CSP_FRAME_SRC = ("http://159.89.22.211:80",)

MIDDLEWARE = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "authentication.middleware.LogIPMiddleware",
    "authentication.middleware.LoginRedirectMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# INTERNAL_IPS = [
#     # ... your IP addresses ...
#     '127.0.0.1',
#     '172.17.0.1',
#     # If using Docker, you might need to add '172.17.0.1' or similar.
# ]
# if DEBUG:
#     import socket  # only if you haven't already imported this
#     hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
#     INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


OWNER_ID = os.getenv("OWNER_ID")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
STYLE_ID = os.getenv("STYLE_ID")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
DEFAULT_EMAIL_DOMAIN = os.getenv("DEFAULT_EMAIL_DOMAIN")
DEFAULT_USER_CREATION_PASSWORD = os.getenv("DEFAULT_USER_CREATION_PASSWORD")
DEFAULT_PHONE = os.getenv("DEFAULT_PHONE")
BASE_URL = os.getenv("BASE_URL")
BASE_URL_PRIV_KUNDEN = os.getenv("BASE_URL_PRIV_KUNDEN")
REFRESH_URL = os.getenv("REFRESH_URL")
POST_ANGEBOT_URL = os.getenv("POST_ANGEBOT_URL")
ACCESS_TOKEN_URL = os.getenv("ACCESS_TOKEN_URL")
ZOHO_ACCESS_TOKEN = os.getenv("ZOHO_ACCESS_TOKEN")
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
SERVER_UPLINK_KEY = os.getenv("SERVER_UPLINK_KEY")
CLIENT_UPLINK_KEY = os.getenv("CLIENT_UPLINK_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", default="openaikey")
DEVELOPEMENT_MODE = os.getenv(f"DEVELOPEMENT")
TELEBOT_TOKEN = os.getenv("TELEBOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TELEGRAM_LOGGING = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", default="support_4"),
        "USER": os.getenv("POSTGRES_USER", default="support_1"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", default="support1234"),
        "HOST": os.getenv("POSTGRES_HOST", default="localhost"),
        "PORT": int(os.getenv("POSTGRES_PORT", default="5433")),
    }
}
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
LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "media/"
MEDIA_PDF_URL = "media/pdf/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#         'file': {
#             'class': 'logging.FileHandler',
#             'filename': 'django_debug.log',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console', 'file'],
#             'level': 'DEBUG',  # Установите уровень логирования на DEBUG для максимальной детализации
#             'propagate': True,
#         },
#         # Для логирования запросов к Django
#         'django.request': {
#             'handlers': ['console', 'file'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         # Вы можете добавить другие логгеры для других частей вашего приложения
#     },
# }



# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'juno.dyntcb.de'
# EMAIL_PORT =  '8843'
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
# EMAIL_HOST_USER = 'si@juno-solar.com'
# EMAIL_HOST_PASSWORD = '301c81Pq8'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# EMAIL_HOST = 'send.one.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'teamit@juno-solar.com'
# EMAIL_HOST_PASSWORD = 'ef1869Zb3'
# Credentials for the SMTP server
