from django.http import HttpResponseNotFound
import logging
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

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


class LoginRedirectMiddleware(MiddlewareMixin):
    def __call__(self, request):
        # Get the current path
        current_path = request.get_full_path()
        # Check if it is login without next parameter
        if current_path == "/login" and "next=" not in request.GET:
            return redirect(f"{current_path}/?next=/")
        # Otherwise, just call the next middleware in the chain
        return self.get_response(request)
