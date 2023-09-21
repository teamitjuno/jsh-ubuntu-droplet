from django.apps import AppConfig
import logging
from django.http import Http404


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"


logger = logging.getLogger("django.request")


def skip_404s(record):
    if record.exc_info:
        exc_value = record.exc_info[1]
        if isinstance(exc_value, Http404):
            if (
                "/.env" in record.getMessage()
                or "/wp-login.php" in record.getMessage()
                or "/.git/config" in record.getMessage()
            ):
                return False
    return True


logger.addFilter(skip_404s)
