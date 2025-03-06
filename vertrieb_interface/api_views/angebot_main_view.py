import os, json

# Django related imports
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import View
from django.views.generic.edit import FormMixin

# Local imports from 'config'
from config.settings import TELEGRAM_LOGGING

# Local imports from 'vertrieb_interface'
from vertrieb_interface.forms import (
    VertriebAngebotForm,
)
from vertrieb_interface.zoho_api_connector import (
    pushAngebot,
    put_form_data_to_zoho_jpp,
    fetch_user_angebote_all,
)
from vertrieb_interface.models import CustomLogEntry, VertriebAngebot
from vertrieb_interface.telegram_logs_sender import (
    send_message_to_bot,
    send_custom_message,
)
from vertrieb_interface.api_views.common import load_json_data, update_list
from vertrieb_interface.api_views.auth_checkers import VertriebCheckMixin


class AngebotEditView(LoginRequiredMixin, VertriebCheckMixin, FormMixin, View):
    model = VertriebAngebot
    form_class = VertriebAngebotForm
    template_name = "vertrieb/edit_angebot.html"
    context_object_name = "vertrieb_angebot"

    def dispatch(self, request, *args, **kwargs):
        angebot_id = kwargs.get("angebot_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        vertrieb_angebot = self.model.objects.get(angebot_id=angebot_id)
        reload = vertrieb_angebot.name_display_value == "None None"
        self.handle_status_change(angebot_id, reload)

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(self.model, angebot_id=self.kwargs.get("angebot_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vertrieb_angebot = self.get_object()

        user = self.request.user
        # vertrieb_angebot = self.model.objects.get(angebot_id=angebot_id, user=user)
        form = self.form_class(instance=vertrieb_angebot, user=user)
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

        context = {
            "countdown": vertrieb_angebot.countdown(),
            "messages": messages.get_messages(self.request),
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
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def handle_status_change(self, angebot_id, reload):
        user = self.request.user
        if reload:
            all_user_angebots_list = fetch_user_angebote_all(self.request)
            user.zoho_data_text = json.dumps(all_user_angebots_list)
            user.save()

        for angebot in self.model.objects.filter(
            angebot_id=angebot_id, status="bekommen"
        ):
            if angebot.status_change_field:
                if (
                    timezone.now() - angebot.status_change_field
                ).total_seconds() >= 14 * 24 * 60 * 60:
                    angebot.status = "abgelaufen"
                    angebot.save()

                    CustomLogEntry.objects.log_action(
                        user_id=angebot.user_id,
                        content_type_id=ContentType.objects.get_for_model(angebot).pk,
                        object_id=angebot.pk,
                        object_repr=str(angebot),
                        action_flag=CHANGE,
                        status=angebot.status,
                    )

    def get(self, request, angebot_id, *args, **kwargs):
        user = request.user
        vertrieb_angebot = self.model.objects.get(angebot_id=angebot_id, user=user)
        form = self.form_class(instance=vertrieb_angebot, user=user)
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

        context = {
            "countdown": vertrieb_angebot.countdown(),
            "messages": messages.get_messages(request),
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
        user_zoho_id = user.zoho_id
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)
        instance = form.instance
        if request.method == "POST":
            action_type = request.POST.get("action_type")
            if action_type == "switch_to_bekommen":
                if form.is_valid():
                    instance.angebot_id_assigned = True
                    instance.is_locked = True
                    instance.status = "bekommen"
                    form.save()
                    self.push_and_save_angebot(
                        vertrieb_angebot, user_zoho_id, form, request
                    )
                    if TELEGRAM_LOGGING:
                        send_message_to_bot(
                            f"{user.first_name} {user.last_name} hat ein PDF Angebot für einen Kunden erstellt. Kunde: {vertrieb_angebot.name}"
                        )
                    return redirect(
                        "vertrieb_interface:create_angebot_pdf_user",
                        vertrieb_angebot.angebot_id,
                    )
            elif action_type == "switch_to_bekommen_pdf_plus_kalk":
                if form.is_valid():
                    instance.angebot_id_assigned = True
                    instance.is_locked = True
                    instance.status = "bekommen"
                    form.save()
                    self.push_and_save_angebot(
                        vertrieb_angebot, user_zoho_id, form, request
                    )

                    if TELEGRAM_LOGGING:
                        send_custom_message(
                            user,
                            "hat ein PDF Angebot für einen Interessenten erstellt.",
                            f"Kunde: {vertrieb_angebot.name} 📑",
                        )
                    return redirect(
                        "vertrieb_interface:create_angebot_and_calc_pdf",
                        vertrieb_angebot.angebot_id,
                    )
            elif action_type == "zahlungs":

                if form.is_valid():
                    instance.zahlungsbedingungen = form.cleaned_data[
                        "zahlungsbedingungen"
                    ]
                    instance.save(update_fields=["zahlungsbedingungen"])

                    return redirect(
                        "vertrieb_interface:create_angebot_pdf_user",
                        vertrieb_angebot.angebot_id,
                    )
            elif action_type == "kalkulation_erstellen":

                if form.is_valid():
                    form.save()
                    return redirect(
                        "vertrieb_interface:create_calc_pdf",
                        vertrieb_angebot.angebot_id,
                    )

            elif action_type == "angebotsumme_rechnen":
                if form.is_valid():
                    form.save()

            elif action_type == "save":
                if form.is_valid():
                    if TELEGRAM_LOGGING:
                        send_custom_message(
                            user,
                            "hat macht Speichern",
                            f"Kunde: {vertrieb_angebot.name} 📑",
                        )
                    instance.angebot_id_assigned = True

                    zoho_id = instance.zoho_id
                    angebot_existing = self.model.objects.filter(
                        user=user,
                        angebot_id_assigned=True,
                        zoho_id=zoho_id,
                    ).exclude(status="bekommen")

                    if angebot_existing.count() != 0:
                        extracted_part = (
                            str(angebot_existing)
                            .split("VertriebAngebot: ")[1]
                            .split(">]")[0]
                        )
                        if vertrieb_angebot.angebot_id == extracted_part:
                            # instance.save()
                            form.fill_geo_coordinates()
                            form.save()
                            put_form_data_to_zoho_jpp(form)
                            CustomLogEntry.objects.log_action(
                                user_id=vertrieb_angebot.user_id,
                                content_type_id=ContentType.objects.get_for_model(
                                    vertrieb_angebot
                                ).pk,
                                object_id=vertrieb_angebot.pk,
                                object_repr=str(vertrieb_angebot),
                                action_flag=CHANGE,
                                status=vertrieb_angebot.status,
                            )
                            return redirect(
                                "vertrieb_interface:edit_angebot",
                                vertrieb_angebot.angebot_id,
                            )

                        else:
                            form.add_error(
                                None,
                                f"Sie können dieses Angebot nicht speichern, da Sie in Ihrer Liste bereits das Angebot {extracted_part} mit einem leeren Status für diesen Interessenten haben.\nEntweder schließen Sie die Erstellung des Angebots ab, indem Sie ein PDF-Dokument erstellen.\nOder löschen Sie das unfertige Angebot.\n",
                            )
                            return self.form_invalid(form, vertrieb_angebot, request)
                    else:
                        instance.save()
                        form.fill_geo_coordinates()
                        form.save()
                        put_form_data_to_zoho_jpp(form)

                        CustomLogEntry.objects.log_action(
                            user_id=vertrieb_angebot.user_id,
                            content_type_id=ContentType.objects.get_for_model(
                                vertrieb_angebot
                            ).pk,
                            object_id=vertrieb_angebot.pk,
                            object_repr=str(vertrieb_angebot),
                            action_flag=CHANGE,
                            status=vertrieb_angebot.status,
                        )
                    return redirect(
                        "vertrieb_interface:edit_angebot",
                        vertrieb_angebot.angebot_id,
                    )

            return self.form_invalid(form, vertrieb_angebot, request)

    def push_and_save_angebot(self, vertrieb_angebot, user_zoho_id, form, request):
        """
        Attempts to push an Angebot to ZOHO and save the response.
        In case of any exception, adds an error to the form and returns a form invalid response.

        """
        try:
            response = pushAngebot(vertrieb_angebot, user_zoho_id)
            response_data = response.json()
            new_record_id = response_data["data"]["ID"]
            vertrieb_angebot.angebot_zoho_id = new_record_id
            vertrieb_angebot.save()
        except Exception as e:
            error_message = f"ZOHO connection Fehler: {str(e)}"
            form.add_error(None, error_message)
            return self.form_invalid(form, vertrieb_angebot, request)

    def form_invalid(self, form, vertrieb_angebot, request, *args, **kwargs):
        context = self.get_context_data()
        context["status_change_field"] = vertrieb_angebot.status_change_field
        context["countdown"] = vertrieb_angebot.countdown()
        context["messages"] = messages.get_messages(request)
        context["vertrieb_angebot"] = vertrieb_angebot
        context["form"] = form
        return render(self.request, self.template_name, context)
