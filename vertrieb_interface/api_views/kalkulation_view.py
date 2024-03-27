# Python standard libraries
import os, json

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
    VertriebAngebotForm,
)
from vertrieb_interface.zoho_api_connector import (
    pushTicket,
)
from vertrieb_interface.models import VertriebAngebot

from vertrieb_interface.telegram_logs_sender import (
    send_custom_message,
)
from vertrieb_interface.api_views.auth_checkers import VertriebCheckMixin


class KalkulationEditView(LoginRequiredMixin, VertriebCheckMixin, FormMixin, View):
    model = VertriebAngebot
    form_class = VertriebAngebotForm
    template_name = "vertrieb/edit_calc.html"
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
        vertrieb_angebot = self.model.objects.get(
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
            self.model, angebot_id=self.kwargs.get("angebot_id")
        )
        user = request.user
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)
        if "pdf_erstellen" in request.POST:
            if form.is_valid():
                vertrieb_angebot.angebot_id_assigned = True

                data = json.loads(user.zoho_data_text or '[["test", "test"]]')
                name_to_kundennumer = {
                    item["name"]: item["zoho_kundennumer"] for item in data
                }
                name_to_zoho_id = {item["name"]: item["zoho_id"] for item in data}
                name = form.cleaned_data["name"]
                zoho_id = form.cleaned_data["zoho_id"]
                kundennumer = name_to_kundennumer[name]

                zoho_id = name_to_zoho_id[name]

                vertrieb_angebot.zoho_kundennumer = kundennumer
                vertrieb_angebot.zoho_id = int(zoho_id)
                vertrieb_angebot.save()
                form.save()  # type:ignore
                if TELEGRAM_LOGGING:
                    send_custom_message(
                        user,
                        "hat eine PDF Kalkulation für einen Interessenten erstellt.",
                        f"Kunde: {vertrieb_angebot.name} 📊",
                    )

                return redirect(
                    "vertrieb_interface:create_calc_pdf", vertrieb_angebot.angebot_id
                )
        elif form.is_valid():
            vertrieb_angebot.angebot_id_assigned = True

            data = json.loads(user.zoho_data_text or '[["test", "test"]]')
            name_to_kundennumer = {
                item["name"]: item["zoho_kundennumer"] for item in data
            }
            name_to_zoho_id = {item["name"]: item["zoho_id"] for item in data}
            name = form.cleaned_data["name"]
            zoho_id = form.cleaned_data["zoho_id"]
            kundennumer = name_to_kundennumer[name]

            zoho_id = name_to_zoho_id[name]

            vertrieb_angebot.zoho_kundennumer = kundennumer
            vertrieb_angebot.zoho_id = int(zoho_id)
            vertrieb_angebot.save()
            form.save()  # type:ignore

            return redirect("vertrieb_interface:edit_calc", vertrieb_angebot.angebot_id)
        return self.form_invalid(form, vertrieb_angebot)

    def form_invalid(self, form, vertrieb_angebot, *args, **kwargs):
        context = self.get_context_data()

        context["status_change_field"] = vertrieb_angebot.status_change_field

        context["vertrieb_angebot"] = vertrieb_angebot
        context["form"] = form

        return render(self.request, self.template_name, context)
