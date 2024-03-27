# Python standard libraries
import os

# Django related imports
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from django.views.generic.edit import FormMixin

# Local imports from 'config'
from config.settings import TELEGRAM_LOGGING

# Local imports from 'vertrieb_interface'
from vertrieb_interface.forms import (
    TicketForm,
)
from vertrieb_interface.zoho_api_connector import (
    pushTicket,
)
from vertrieb_interface.models import VertriebAngebot

from vertrieb_interface.telegram_logs_sender import (
    send_custom_message,
)
from vertrieb_interface.api_views.auth_checkers import VertriebCheckMixin


class TicketEditView(LoginRequiredMixin, VertriebCheckMixin, FormMixin, View):
    model = VertriebAngebot
    form_class = TicketForm
    template_name = "vertrieb/edit_ticket.html"
    context_object_name = "vertrieb_angebot"

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(self.model, angebot_id=self.kwargs.get("angebot_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vertrieb_angebot = self.get_object()

        context["form"] = self.form_class(
            instance=vertrieb_angebot, user=self.request.user
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get(self, request, angebot_id, *args, **kwargs):
        vertrieb_angebot = VertriebAngebot.objects.get(
            angebot_id=angebot_id, user=request.user
        )
        form = self.form_class(instance=vertrieb_angebot, user=request.user)
        user = request.user
        user_folder = os.path.join(
            settings.MEDIA_ROOT, f"pdf/usersangebots/{user.username}/Kalkulationen/"
        )
        calc_image = os.path.join(user_folder, "tmp.png")
        calc_image_suffix = os.path.join(
            user_folder, "calc_tmp_" + f"{vertrieb_angebot.angebot_id}.png"
        )
        relative_path = os.path.relpath(calc_image, start=settings.MEDIA_ROOT)
        relative_path_suffix = os.path.relpath(
            calc_image_suffix, start=settings.MEDIA_ROOT
        )
        context = self.get_context_data()

        context = {
            "user": user,
            "vertrieb_angebot": vertrieb_angebot,
            "form": form,
            "calc_image": relative_path,
            "calc_image_suffix": relative_path_suffix,
            "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
            "OWNER_ID": settings.OWNER_ID,
            "STYLE_ID": settings.STYLE_ID,
            "LATITUDE": vertrieb_angebot.postanschrift_latitude,
            "LONGITUDE": vertrieb_angebot.postanschrift_longitude,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        vertrieb_angebot = get_object_or_404(
            VertriebAngebot, angebot_id=self.kwargs.get("angebot_id")
        )
        user = request.user
        user_zoho_id = user.zoho_id
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)
        if "pdf_erstellen" in request.POST:
            if form.is_valid():
                vertrieb_angebot.angebot_id_assigned = True
                vertrieb_angebot.save()
                form.save()  # type:ignore
                response = pushTicket(vertrieb_angebot, user_zoho_id)
                if TELEGRAM_LOGGING:
                    send_custom_message(
                        user,
                        "Response",
                        f"{response} 🎟️",
                    )
                if TELEGRAM_LOGGING:
                    send_custom_message(
                        user,
                        "hat ein PDF Ticket für einen Kunden erstellt.",
                        f"Kunde: {vertrieb_angebot.name} 🎟️",
                    )
                return redirect(
                    "vertrieb_interface:create_ticket_pdf", vertrieb_angebot.angebot_id
                )

        elif form.is_valid():
            instance = form.instance

            instance.save()
            form.save()

        return self.form_invalid(form, vertrieb_angebot)

    def form_invalid(self, form, vertrieb_angebot, *args, **kwargs):
        context = self.get_context_data()

        context["status_change_field"] = vertrieb_angebot.status_change_field

        context["vertrieb_angebot"] = vertrieb_angebot
        context["form"] = form

        return render(self.request, self.template_name, context)
