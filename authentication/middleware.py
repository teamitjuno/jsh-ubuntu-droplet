from django.http import HttpResponseNotFound
import logging

logger = logging.getLogger(__name__)


class LogIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, HttpResponseNotFound):
            ip = self.get_client_ip(request)
            path = request.path
            logger.warning(f"Not found: {path}, IP Address: {ip}")
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
