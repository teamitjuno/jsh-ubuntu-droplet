# Django related imports

from django.contrib import messages


from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, get_connection

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView

# Local imports from 'config'
from config.settings import EMAIL_BACKEND

# Local imports from 'datenblatter'
from datenblatter.models import Datenblatter
from prices.models import SolarModulePreise

# Local imports from 'vertrieb_interface'
from vertrieb_interface.forms import (
    VertriebAngebotEmailForm,
)
from vertrieb_interface.models import VertriebAngebot

import logging

logger = logging.getLogger(__name__)


class DocumentAndCalcView(LoginRequiredMixin, DetailView):
    model = VertriebAngebot
    template_name = "vertrieb/document_and_calc_view.html"
    context_object_name = "vertrieb_angebot"
    pk_url_kwarg = "angebot_id"
    form_class = VertriebAngebotEmailForm

    def dispatch(self, request, *args, **kwargs):
        angebot_id = kwargs.get("angebot_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        angebot_id = self.kwargs.get(self.pk_url_kwarg)
        self.object = get_object_or_404(self.model, angebot_id=angebot_id)
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vertrieb_angebot = self.get_object()
        angebot_id = self.kwargs.get("angebot_id")
        pdf_url = reverse(
            "vertrieb_interface:serve_pdf", args=[angebot_id]
        )
        context["pdf_url"] = pdf_url
        context["angebot_id"] = angebot_id
        context["form"] = self.form_class(
            instance=vertrieb_angebot, user=self.request.user
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(
            request.POST, instance=self.get_object(), user=request.user
        )

        if form.is_valid():
            form.save()
            if self._send_email(form.instance):
                messages.success(request, "Email sent successfully")
                email_sent = True
                return redirect(
                    "vertrieb_interface:document_and_calc_view",
                    form.instance.angebot_id,
                )

        return self.form_invalid(form)

    def _send_email(self, vertrieb_angebot):
        datenblatter = get_object_or_404(Datenblatter)
        email_address = self.request.POST.get("email")
        email_content = self.request.POST.get("text_for_email")
        subject = f"Angebot Photovoltaikanlage {vertrieb_angebot.angebot_id}"

        user = self.request.user
        body = f"{email_content}\n\n{user.smtp_body}"
        user_email = user.email

        try:
            connection = get_connection(
                backend=EMAIL_BACKEND,
                host=user.smtp_server,
                port=user.smtp_port,
                username=user.smtp_username,
                password=user.smtp_password,
                use_tls=True,
                fail_silently=False,
            )
            email = EmailMultiAlternatives(
                subject,
                body,
                user.smtp_username,
                [email_address, user_email],
                connection=connection,
            )
            self._attach_files(email, vertrieb_angebot, datenblatter)
            email.send()
            return True
        except Exception as e:
            messages.error(self.request, f"Failed to send email: {str(e)}")
            return False

    def _attach_files(self, email, vertrieb_angebot, datenblatter):
        file_data = vertrieb_angebot.angebot_pdf.tobytes()
        name = replace_spaces_with_underscores(vertrieb_angebot.name)
        email.attach(
            f"{name}_{vertrieb_angebot.angebot_id}.pdf", file_data, "application/pdf"
        )

        if vertrieb_angebot.datenblatter_solar_module:
            self._attach_datenblatt_from_prices(
                email,
                SolarModulePreise.objects.get(name=vertrieb_angebot.solar_module).datenblatt,
                SolarModulePreise.objects.get(name=vertrieb_angebot.solar_module).filename,
            )

        if vertrieb_angebot.datenblatter_optimizer:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, "optimizer", "Huawei Optimizer")
            else:
                self._attach_datenblatter(email, datenblatter, "optimizer_viessmann", "VIESSMANN Optimizer")
                self._attach_datenblatter(email, datenblatter, "viessmann_tigo", "VIESSMANN Tigo")

        if vertrieb_angebot.datenblatter_speichermodule:
            if vertrieb_angebot.hersteller == "Huawei":
                if vertrieb_angebot.speicher_model == "LUNA 2000-5-S0":
                    self._attach_datenblatter(email, datenblatter, "speicher_module", "Huawei S0 Speicher 5kWh")
                elif vertrieb_angebot.speicher_model == "LUNA 2000-7-S1":
                    self._attach_datenblatter(email, datenblatter, "speicher_module_huawei7", "Huawei S1 Speicher 7kWh")
            else:
                self._attach_datenblatter(
                    email, datenblatter, "speicher_module_viessmann", "VIESSMANN Speicher"
                )

        if vertrieb_angebot.datenblatter_smartmeter:
            if vertrieb_angebot.smartmeter_model == "Smart Power Sensor DTSU666H":
                self._attach_datenblatter(email, datenblatter, "huawei_smartmeter_dtsu", "Smart Power Sensor")
            elif vertrieb_angebot.smartmeter_model == "EMMA-A02":
                self._attach_datenblatter(email, datenblatter, "huawei_smartmeter_emma", "EMMA-A02")

        if vertrieb_angebot.datenblatter_wechselrichter:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, "wechselrichter", "Huawei Wechselrichter")

        if vertrieb_angebot.datenblatter_wallbox:
            self._attach_datenblatt_from_prices(
                email,
                WallBoxPreise.objects.get(name=vertrieb_angebot.wallboxtyp).datenblatt,
                WallBoxPreise.objects.get(name=vertrieb_angebot.wallboxtyp).filename,
            )

        if vertrieb_angebot.datenblatter_backup_box:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, "backup_box", "Huawei Backup Box")

        if vertrieb_angebot.hersteller == "Viessmann":
            self._attach_datenblatter(
                email, datenblatter, "viessmann_allgemeine_bedingungen", "VIESSMANN Allgemeine Bedingungen"
            )
            self._attach_datenblatter(
                email, datenblatter, "viessmann_versicherung_ausweis", "VIESSMANN Versicherungsausweis"
            )
        if vertrieb_angebot.finanzierung:
            self._attach_datenblatter(email, datenblatter, "finanzierung", "Flyer_Finanzierung_by_CLOOVER")

    def _attach_datenblatter(self, email, datenblatter, field, filename):
        """
        Anhängen von Datenblättern zu einer E-Mail.

        Diese Methode geht durch die angegebenen Felder, liest die entsprechenden Datenblätter,
        und fügt sie als PDF-Anhänge an die E-Mail an.

        Args:
            email: Das E-Mail-Objekt, zu dem die Anhänge hinzugefügt werden sollen.
            datenblatter: Ein Objekt, das die Datenblätter enthält.
            fields: Eine Feldname, der dem Attributen in datenblatter entspricht, dessen
                    Datenblatt angehängt werden soll.
            filename: Eine Name, den die angehängte Datei erhalten soll

        Raises:
            AttributeError: Wenn ein angegebenes Feld nicht in datenblatter existiert.
            IOError: Wenn das Datenblatt nicht geöffnet oder gelesen werden kann.
            Exception: Allgemeine Ausnahmebehandlung für unerwartete Fehler.
        """
        try:
            datenblatt = getattr(datenblatter, field, None)
            if not datenblatt:
                raise AttributeError(
                    f"{field} attribute is missing in datenblatter object."
                )

            with datenblatt.open("rb") as file:
                file_data = file.read()

            email.attach(f"{filename}.pdf", file_data, "application/pdf")

        except AttributeError as e:
            logger.error(f"Failed to process {field}: {e}")
            raise e  # Optionally re-raise if you want the error to propagate.

        except IOError as e:
            logger.error(
                f"Failed to read or attach {field}.pdf due to a file error: {e}"
            )
            raise e  # Optionally re-raise if the process should not continue on error.

        except Exception as e:
            logger.error(
                f"An unexpected error occurred while processing {field}: {e}"
            )
            raise e  # Optionally re-raise to signify critical failure.

    def _attach_datenblatt_from_prices(self, email, datenblatt, filename):
        """
        Anhängen von Datenblättern zu einer E-Mail.

        Diese Methode geht durch die angegebenen Felder, liest die entsprechenden Datenblätter,
        und fügt sie als PDF-Anhänge an die E-Mail an.

        Args:
            email: Das E-Mail-Objekt, zu dem die Anhänge hinzugefügt werden sollen.
            solarmodul: Das Datenblatt.
            filename: Eine Name, den die angehängte Datei erhalten soll

        Raises:
            AttributeError: Wenn ein angegebenes Feld nicht in datenblatter existiert.
            IOError: Wenn das Datenblatt nicht geöffnet oder gelesen werden kann.
            Exception: Allgemeine Ausnahmebehandlung für unerwartete Fehler.
        """
        try:
            if not datenblatt:
                raise AttributeError(
                    f"{solarmodul} is missing."
                )

            with datenblatt.open("rb") as file:
                file_data = file.read()

            email.attach(f"{filename}.pdf", file_data, "application/pdf")

        except AttributeError as e:
            logger.error(f"Failed to process {solarmodul}: {e}")
            raise e  # Optionally re-raise if you want the error to propagate.

        except IOError as e:
            logger.error(
                f"Failed to read or attach {solarmodul}.pdf due to a file error: {e}"
            )
            raise e  # Optionally re-raise if the process should not continue on error.

        except Exception as e:
            logger.error(
                f"An unexpected error occurred while processing {solarmodul}: {e}"
            )
            raise e  # Optionally re-raise to signify critical failure.

    def form_invalid(self, form):
        return render(
            self.request, self.template_name, self.get_context_data(form=form)
        )


def replace_spaces_with_underscores(s: str) -> str:
    return s.replace(" ", "_").replace(",","")
