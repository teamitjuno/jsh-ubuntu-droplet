# Django related imports
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

# Local imports from 'config'
from config.settings import TELEGRAM_LOGGING

from vertrieb_interface.models import VertriebTicket

from vertrieb_interface.telegram_logs_sender import (
    send_custom_message,
)
from vertrieb_interface.api_views.auth_checkers import VertriebCheckMixin


class ViewOrdersTicket(LoginRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebTicket
    template_name = "vertrieb/view_orders_ticket.html"
    context_object_name = "tickets"

    def get_queryset(self):
        # Optimized query to directly exclude "angenommen" and "bekommen" statuses
        return self.model.objects.filter(
            user=self.request.user, is_locked=False
        )#.exclude(status__in=["angenommen"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if TELEGRAM_LOGGING:
            send_custom_message(
                self.request.user, "Accessed the offers list page.", "Info"
            )
        return context
