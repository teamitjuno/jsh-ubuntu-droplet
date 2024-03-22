# Python standard libraries
import asyncio
import datetime
import json
import os
from time import sleep
from urllib.parse import unquote

# Django related imports
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Count, IntegerField, Q, Sum, Case, When, Value
from django.db.models.functions import Cast
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.formats import date_format
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.defaults import page_not_found
from django.views.generic import DeleteView, DetailView, ListView, UpdateView, View
from django.views.generic.edit import FormMixin

# Local imports from 'config'
from config import settings as local_settings
from config.settings import EMAIL_BACKEND, TELEGRAM_LOGGING

# Local imports from 'prices'
from prices.models import SolarModulePreise

# Local imports from 'calculator'
from calculator.models import Calculator
from calculator.forms import CalculatorForm

# Local imports from 'datenblatter'
from datenblatter.models import Datenblatter

# Local imports from 'shared'
from shared.chat_bot import handle_message

# Local imports from 'vertrieb_interface'
from vertrieb_interface.forms import (
    VertriebAngebotForm,
    VertriebAngebotEmailForm,
    TicketForm,
)
from vertrieb_interface.get_user_angebots import (
    delete_redundant_angebot,
    extract_values,
    fetch_angenommen_status,
    fetch_user_angebote_all,
    log_and_notify,
    pushAngebot,
    put_form_data_to_zoho_jpp,
)
from vertrieb_interface.models import CustomLogEntry, VertriebAngebot
from vertrieb_interface.pdf_services import (
    angebot_pdf_creator,
    angebot_pdf_creator_user,
    angebot_plus_calc_pdf,
    calc_pdf_creator,
    ticket_pdf_creator,
)
from vertrieb_interface.permissions import admin_required, AdminRequiredMixin
from vertrieb_interface.telegram_logs_sender import send_message_to_bot
from vertrieb_interface.utils import load_vertrieb_angebot

# Local imports from 'authentication'
from authentication.models import User
from authentication.forms import InitialAngebotDataViewForm


def generate_angebot_id(request):
    user = User.objects.get(id=request.user.pk)
    kurz = user.kuerzel
    current_datetime = datetime.datetime.now()
    return f"AN-{kurz}{current_datetime.strftime('%d%m%Y-%H%M%S')}"


class AsyncBytesIter:
    def __init__(self, byte_data, chunk_size=8192):
        self.byte_data = byte_data
        self.chunk_size = chunk_size
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):

        if self.index >= len(self.byte_data):
            raise StopAsyncIteration

        chunk = self.byte_data[self.index : self.index + self.chunk_size]
        self.index += self.chunk_size
        return chunk


class AsyncFileIter:
    def __init__(self, file, chunk_size=8192):
        self.file = file
        self.chunk_size = chunk_size
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if isinstance(self.file, memoryview):

            if self.index >= len(self.file):
                raise StopAsyncIteration

            chunk = self.file[self.index : self.index + self.chunk_size]
            self.index += self.chunk_size
        else:
            chunk = await asyncio.to_thread(self.file.read, self.chunk_size)

            if not chunk:
                raise StopAsyncIteration

        return chunk


now = timezone.now()
now_localized = timezone.localtime(now)
now_german = date_format(now_localized, "DATETIME_FORMAT")


# Funktion zum Senden von Benachrichtigungen mit verbesserter Nachrichtenstruktur
def send_custom_message(user, action, details):
    """
    Sendet eine benutzerdefinierte Nachricht über den Bot.

    :param user: Das User-Objekt, das die Aktion ausführt.
    :param action: Eine kurze Beschreibung der Aktion.
    :param details: Details zur Aktion, z.B. was erstellt wurde und für wen.
    """
    user_name = f"{user.first_name} {user.last_name}".strip()
    user_name = user_name if user_name else "Ein Benutzer"

    message = f"{user_name} {action} {details}"
    send_message_to_bot(message)


def handler404(request, exception):
    return render(request, "404.html", status=404)


def vertrieb_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class VertriebCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return vertrieb_check(self.request.user)  # type: ignore


def get_recent_activities(user):
    recent_activities = (
        CustomLogEntry.objects.filter(user_id=user.id)
        .select_related("content_type", "user")
        .order_by("-action_time")[:15]
    )

    activities = []
    for entry in recent_activities:
        vertrieb_angebot = entry.get_vertrieb_angebot()
        if vertrieb_angebot:
            status = (
                vertrieb_angebot.status if vertrieb_angebot else "noch nicht zugeordnet"
            )
            kundenname = (
                vertrieb_angebot.vorname_nachname if vertrieb_angebot else "keine"
            )
            activity = {
                "action_time": entry.action_time,
                "module": entry.content_type.model_class()._meta.verbose_name_plural,
                "action": {
                    "message": entry.get_change_message(),
                    "class": (
                        "text-danger"
                        if entry.get_vertrieb_angebot().status == "abgelaufen"
                        else (
                            "text-warning"
                            if entry.get_vertrieb_angebot().status == "bekommen"
                            else (
                                "text-success"
                                if entry.get_vertrieb_angebot().status == "angenommen"
                                else (
                                    "text-primary"
                                    if entry.action_flag == ADDITION
                                    else (
                                        "text-info"
                                        if entry.action_flag == CHANGE
                                        else "text-danger"
                                    )
                                )
                            )
                        )
                    ),
                },
                "user": entry.user,
                "object": {
                    "repr": entry.object_repr,
                    "class": (
                        "text-danger"
                        if entry.get_vertrieb_angebot().status == "abgelaufen"
                        else (
                            "text-warning"
                            if entry.get_vertrieb_angebot().status == "bekommen"
                            else (
                                "text-success"
                                if entry.get_vertrieb_angebot().status == "angenommen"
                                else (
                                    "text-primary"
                                    if entry.action_flag == ADDITION
                                    else (
                                        "text-info"
                                        if entry.action_flag == CHANGE
                                        else "text-danger"
                                    )
                                )
                            )
                        )
                    ),
                },
                "icon": (
                    "mdi-delete bg-danger-lighten text-danger"
                    if entry.get_vertrieb_angebot().status == "abgelaufen"
                    else (
                        "mdi-minus bg-warning-lighten text-warning"
                        if entry.get_vertrieb_angebot().status == "bekommen"
                        else (
                            "mdi-update bg-success-lighten text-success"
                            if entry.get_vertrieb_angebot().status == "angenommen"
                            else (
                                "mdi-plus bg-primary-lighten text-primary"
                                if entry.action_flag == ADDITION
                                else (
                                    "mdi-update bg-info-lighten text-info"
                                    if entry.action_flag == CHANGE
                                    else "mdi-delete bg-danger-lighten text-danger"
                                )
                            )
                        )
                    )
                ),
                "status": status,
                "kundenname": kundenname,
            }
            if not any(
                a["action_time"] == activity["action_time"]
                or a["object"] == activity["object"]
                for a in activities
            ):
                activities.append(activity)

    return activities


def get_class_based_on_status(entry, status):
    class_map = {
        "abgelaufen": "text-danger",
        "bekommen": "text-warning",
        "angenommen": "text-success",
        ADDITION: "text-primary",
        CHANGE: "text-info",
        DELETION: "text-danger",
    }
    return class_map.get(status, "text-danger")


def get_icon_based_on_status(entry, status):
    icon_map = {
        "abgelaufen": "mdi-delete bg-danger-lighten text-danger",
        "bekommen": "mdi-minus bg-warning-lighten text-warning",
        "angenommen": "mdi-update bg-success-lighten text-success",
        ADDITION: "mdi-plus bg-primary-lighten text-primary",
        CHANGE: "mdi-update bg-info-lighten text-info",
        DELETION: "text-danger",
    }
    return icon_map.get(status, "mdi-delete bg-danger-lighten text-danger")


@user_passes_test(vertrieb_check)
def home(request):
    user = request.user
    load_user_angebots(request)
    if TELEGRAM_LOGGING:
        send_message_to_bot(
            f"{user.first_name} {user.last_name}:  Der Benutzer befindet sich auf der Startseite 🏠"
        )
    year, month = now.year, now.month

    users = (
        User.objects.filter(beruf="Vertrieb")
        .annotate(
            num_vertriebangebots=Count(
                "vertriebangebot",
                filter=Q(
                    vertriebangebot__current_date__year=year,
                    vertriebangebot__angebot_id_assigned=True,
                ),
            )
        )
        .order_by("-num_vertriebangebots")[:5]
    )

    vertriebangebots = VertriebAngebot.objects.filter(
        user=request.user, angebot_id_assigned=True
    )
    current_user_vertriebangebots = vertriebangebots.count()

    current_user_vertriebangebots_month = VertriebAngebot.objects.filter(
        user=request.user,
        angebot_id_assigned=True,
        current_date__year=year,
        current_date__month=month,
    ).count()

    all_vertrieb_angebots = (
        VertriebAngebot.objects.filter(Q(status="angenommen"), angebot_id_assigned=True)
        .values("solar_module")
        .annotate(total_modulanzahl=Sum("total_anzahl"))
        .order_by("solar_module")
    )

    solar_module_stats = (
        vertriebangebots.filter(Q(status="angenommen"), angebot_id_assigned=True)
        .values("solar_module")
        .annotate(total_modulanzahl=Sum("total_anzahl"))
        .order_by("solar_module")
    )

    solar_module_ticket_stats = (
        vertriebangebots.filter(status="angenommen")
        .values("solar_module")
        .annotate(total_modulanzahl=Sum("modul_anzahl_ticket"))
        .order_by("solar_module")
    )

    statuses = [
        "",
        "angenommen",
        "bekommen",
        "in Kontakt",
        "Kontaktversuch",
        "abgelehnt",
        "abgelaufen",
        "on Hold",
        "storniert",
    ]
    status_counts = {
        status: vertriebangebots.filter(status=status).count() for status in statuses
    }

    remaining_stock = {}
    for solar_module in SolarModulePreise.objects.all():
        total_sold = next(
            (
                item["total_modulanzahl"]
                for item in all_vertrieb_angebots
                if item["solar_module"] == solar_module.name
            ),
            0,
        )

        remaining_stock[solar_module.name] = (
            solar_module.quantity - total_sold
            if solar_module.quantity and total_sold
            else 0
        )

    angenommen_count = vertriebangebots.filter(status="angenommen").count()
    all_count = vertriebangebots.count()
    bekommen_count = vertriebangebots.filter(status="bekommen").count()
    in_kontakt_count = vertriebangebots.filter(status="in Kontakt").count()
    kontaktversuch_count = vertriebangebots.filter(status="Kontaktversuch").count()
    abgelehnt_count = vertriebangebots.filter(status="abgelehnt").count()
    abgelaufen_count = vertriebangebots.filter(status="abgelaufen").count()
    on_hold_count = vertriebangebots.filter(status="on Hold").count()
    storniert_count = vertriebangebots.filter(status="storniert").count()
    lee_count = vertriebangebots.filter(status="").count()

    calculator_instance = Calculator.objects.first()
    if not calculator_instance:
        calculator_instance = Calculator.objects.create(user=user)
    calculator_form = CalculatorForm(instance=calculator_instance, user=user)
    # If it doesn't exist, create one
    if request.method == "POST":
        form = CalculatorForm(request.POST, user=user)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user  # or any user instance you wish to associate
            instance.save()
            return redirect("vertrieb_interface:home")

    context = {
        "users": users,
        "current_user_vertriebangebots_month": current_user_vertriebangebots_month,
        "current_user_vertriebangebots": current_user_vertriebangebots,
        "solar_module_stats": solar_module_stats,
        "activities": get_recent_activities(user),
        "all_count": all_count,
        "calculator_form": calculator_form,
        "calculator_instance": calculator_instance,
        "angenommen": angenommen_count,
        "bekommen": bekommen_count,
        "in_Kontakt": in_kontakt_count,
        "Kontaktversuch": kontaktversuch_count,
        "abgelehnt": abgelehnt_count,
        "abgelaufen": abgelaufen_count,
        "on Hold": on_hold_count,
        "storniert": storniert_count,
        "lee": lee_count,
        "remaining_stock": remaining_stock,
        "solar_module_ticket_stats": solar_module_ticket_stats,
        "all_vertrieb_angebots": all_vertrieb_angebots,
        **status_counts,
    }

    return render(request, "vertrieb/home.html", context)


def filter_bekommen(data):
    return [item for item in data if item.get("status") == "bekommen"]


class TicketCreationView(LoginRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/ticket_creation.html"
    context_object_name = "angebots"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.model.objects.filter(
            user=self.request.user, status="angenommen", angebot_id_assigned=True
        )

        queryset = queryset.annotate(
            zoho_kundennumer_int=Case(
                When(
                    zoho_kundennumer__isnull=False,
                    then=Cast("zoho_kundennumer", IntegerField()),
                ),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        queryset = queryset.order_by("-zoho_kundennumer_int")

        return queryset


def reset_calculator(request):
    user = request.user
    if request.method == "POST":
        form = CalculatorForm(request.POST, user=user)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.modulanzahl = 0
            instance.wallbox_anzahl = 0
            instance.anzOptimizer = 0
            instance.anz_speicher = 0
            instance.angebotsumme = 0
            instance.save()
    return redirect("vertrieb_interface:home")


@user_passes_test(vertrieb_check)
def profile(request, *args, **kwargs):
    user = request.user

    if request.method == "POST":
        initial_data_form = InitialAngebotDataViewForm(
            request.POST, instance=request.user, user=request.user
        )

        if initial_data_form.is_valid():
            initial_data_form.save()
            print((request, "Settings updated successfully!"))
            messages.success(request, "Settings updated successfully!")
            return redirect("vertrieb_interface:profile")
    else:
        print((request, "xyu"))

        initial_data_form = InitialAngebotDataViewForm(
            instance=request.user, user=request.user
        )

    context = {"user": user, "form": initial_data_form}

    return render(request, "vertrieb/profile.html", context)


@user_passes_test(vertrieb_check)
def help(request):
    return render(request, "vertrieb/help.html")


@user_passes_test(vertrieb_check)
@csrf_exempt
def chat_bot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("question", "")

        # Retrieve the thread_id from the session if it exists, else None
        thread_id = request.session.get("thread_id", None)

        # Pass the question and thread_id to the handle_message function
        response, thread_id = handle_message(question, thread_id)

        # Update the thread_id in the session
        request.session["thread_id"] = thread_id

        return JsonResponse({"response": response})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)


@user_passes_test(vertrieb_check)
def user_redirect_view(request):
    if request.user.is_authenticated:
        if request.user.is_home_page:
            load_user_angebots(request)
            return redirect("vertrieb_interface:intermediate_view")
        else:
            return redirect("vertrieb_interface:home")
    else:
        return redirect("authentication:login")


def intermediate_view(request):
    angebot_id = generate_angebot_id(
        request=request
    )  # Or however you obtain the angebot_id

    context = {
        "angebot_id": angebot_id,
    }
    return render(request, "vertrieb/intermediate_template.html", context)


@user_passes_test(vertrieb_check)
def create_angebot_redirect(request):
    if request.method != "POST":
        return page_not_found(request, Exception("POST request required"))

    user = request.user
    angebot_id = request.POST.get("angebot_id")
    initial_data = {
        "verbrauch": user.initial_verbrauch,
        "grundpreis": user.initial_grundpreis,
        "arbeitspreis": user.initial_arbeitspreis,
        "prognose": user.initial_prognose,
        "zeitraum": user.initial_zeitraum,
        "bis10kWp": user.initial_bis10kWp,
        "bis40kWp": user.initial_bis40kWp,
        "anz_speicher": user.initial_anz_speicher,
        "wandhalterung_fuer_speicher": user.initial_wandhalterung_fuer_speicher,
        "ausrichtung": user.initial_ausrichtung,
        "komplex": user.initial_komplex,
        "solar_module": user.initial_solar_module,
        "modulanzahl": user.initial_modulanzahl,
        "garantieWR": user.initial_garantieWR,
        "elwa": user.initial_elwa,
        "thor": user.initial_thor,
        "heizstab": user.initial_heizstab,
        "notstrom": user.initial_notstrom,
        "anzOptimizer": user.initial_anzOptimizer,
        "wallboxtyp": user.initial_wallboxtyp,
        "wallbox_anzahl": user.initial_wallbox_anzahl,
        "kabelanschluss": user.initial_kabelanschluss,
        "text_for_email": user.initial_text_for_email,
        "map_notizen_container_view": user.map_notizen_container_view,
    }

    # Initialize form with POST data
    form_angebot = VertriebAngebotForm(request.POST or initial_data, user=user)
    if form_angebot.is_valid():
        vertrieb_angebot = form_angebot.save(commit=False)
        vertrieb_angebot.created_at = timezone.now()
        vertrieb_angebot.current_date = datetime.datetime.now()

        # Set attributes from user's initial data
        initial_attrs = [
            "verbrauch",
            "grundpreis",
            "arbeitspreis",
            "prognose",
            "zeitraum",
            "bis10kWp",
            "bis40kWp",
            "anz_speicher",
            "wandhalterung_fuer_speicher",
            "ausrichtung",
            "komplex",
            "solar_module",
            "modulanzahl",
            "garantieWR",
            "elwa",
            "thor",
            "heizstab",
            "notstrom",
            "anzOptimizer",
            "wallboxtyp",
            "wallbox_anzahl",
            "kabelanschluss",
            "text_for_email",
        ]
        for attr in initial_attrs:
            setattr(vertrieb_angebot, attr, getattr(user, "initial_" + attr))

        vertrieb_angebot.save(user)
        return redirect("vertrieb_interface:edit_angebot", angebot_id)
    if request.POST and "create_blank_angebot" in request.POST:
        blank_angebot = VertriebAngebot(user=user)
        blank_angebot.created_at = timezone.now()
        blank_angebot.current_date = datetime.datetime.now()
        blank_angebot.verbrauch = user.initial_verbrauch
        blank_angebot.grundpreis = user.initial_grundpreis
        blank_angebot.arbeitspreis = user.initial_arbeitspreis
        blank_angebot.prognose = user.initial_prognose
        blank_angebot.zeitraum = user.initial_zeitraum
        blank_angebot.bis10kWp = user.initial_bis10kWp
        blank_angebot.bis40kWp = user.initial_bis40kWp
        blank_angebot.anz_speicher = user.initial_anz_speicher
        blank_angebot.wandhalterung_fuer_speicher = (
            user.initial_wandhalterung_fuer_speicher
        )
        blank_angebot.ausrichtung = user.initial_ausrichtung
        blank_angebot.komplex = user.initial_komplex
        blank_angebot.solar_module = user.initial_solar_module
        blank_angebot.modulanzahl = user.initial_modulanzahl
        blank_angebot.garantieWR = user.initial_garantieWR
        blank_angebot.elwa = user.initial_elwa
        blank_angebot.thor = user.initial_thor
        blank_angebot.heizstab = user.initial_heizstab
        blank_angebot.notstrom = user.initial_notstrom
        blank_angebot.anzOptimizer = user.initial_anzOptimizer
        blank_angebot.wallboxtyp = user.initial_wallboxtyp
        blank_angebot.wallbox_anzahl = user.initial_wallbox_anzahl
        blank_angebot.kabelanschluss = user.intial_kabelanschluss
        blank_angebot.text_for_email = user.initial_text_for_email
        blank_angebot.save()
        return HttpResponseRedirect(
            reverse("vertrieb_interface:edit_angebot", args=[blank_angebot.angebot_id])
        )

    else:
        print(form_angebot.errors)

        return page_not_found(request, Exception())


@user_passes_test(vertrieb_check)
def create_angebot(request):
    user = request.user

    # Extract initial values from the User model instance
    initial_data = {
        "verbrauch": user.initial_verbrauch,
        "grundpreis": user.initial_grundpreis,
        "arbeitspreis": user.initial_arbeitspreis,
        "prognose": user.initial_prognose,
        "zeitraum": user.initial_zeitraum,
        "bis10kWp": user.initial_bis10kWp,
        "bis40kWp": user.initial_bis40kWp,
        "anz_speicher": user.initial_anz_speicher,
        "wandhalterung_fuer_speicher": user.initial_wandhalterung_fuer_speicher,
        "ausrichtung": user.initial_ausrichtung,
        "komplex": user.initial_komplex,
        "solar_module": user.initial_solar_module,
        "modulanzahl": user.initial_modulanzahl,
        "garantieWR": user.initial_garantieWR,
        "elwa": user.initial_elwa,
        "thor": user.initial_thor,
        "heizstab": user.initial_heizstab,
        "notstrom": user.initial_notstrom,
        "anzOptimizer": user.initial_anzOptimizer,
        "wallboxtyp": user.initial_wallboxtyp,
        "wallbox_anzahl": user.initial_wallbox_anzahl,
        "kabelanschluss": user.initial_kabelanschluss,
        "map_notizen_container_view": user.map_notizen_container_view,
    }

    form_angebot = VertriebAngebotForm(request.POST or initial_data, user=user)

    if TELEGRAM_LOGGING:
        send_custom_message(user, "erstellt ein neues Angebot", "📄")

    if form_angebot.is_valid():
        vertrieb_angebot = form_angebot.save(commit=False)
        vertrieb_angebot.user = user
        vertrieb_angebot.save()
        return redirect("vertrieb_interface:edit_angebot", vertrieb_angebot.angebot_id)

    if request.POST and "create_blank_angebot" in request.POST:
        blank_angebot = VertriebAngebot(user=user)
        blank_angebot.created_at = timezone.now()
        blank_angebot.current_date = datetime.datetime.now()
        blank_angebot.verbrauch = user.initial_verbrauch
        blank_angebot.grundpreis = user.initial_grundpreis
        blank_angebot.arbeitspreis = user.initial_arbeitspreis
        blank_angebot.prognose = user.initial_prognose
        blank_angebot.zeitraum = user.initial_zeitraum
        blank_angebot.bis10kWp = user.initial_bis10kWp
        blank_angebot.bis40kWp = user.initial_bis40kWp
        blank_angebot.anz_speicher = user.initial_anz_speicher
        blank_angebot.wandhalterung_fuer_speicher = (
            user.initial_wandhalterung_fuer_speicher
        )
        blank_angebot.ausrichtung = user.initial_ausrichtung
        blank_angebot.komplex = user.initial_komplex
        blank_angebot.solar_module = user.initial_solar_module
        blank_angebot.modulanzahl = user.initial_modulanzahl
        blank_angebot.garantieWR = user.initial_garantieWR
        blank_angebot.elwa = user.initial_elwa
        blank_angebot.thor = user.initial_thor
        blank_angebot.heizstab = user.initial_heizstab
        blank_angebot.notstrom = user.initial_notstrom
        blank_angebot.anzOptimizer = user.initial_anzOptimizer
        blank_angebot.wallboxtyp = user.initial_wallboxtyp
        blank_angebot.wallbox_anzahl = user.initial_wallbox_anzahl
        blank_angebot.kabelanschluss = user.initial_kabelanschluss
        blank_angebot.text_for_email = user.initial_text_for_email
        blank_angebot.save()
        return HttpResponseRedirect(
            reverse("vertrieb_interface:edit_angebot", args=[blank_angebot.angebot_id])
        )

    if not form_angebot.is_valid():
        # if TELEGRAM_LOGGING:
        #     send_message_to_bot(form_angebot.errors)

        return page_not_found(request, Exception())

    return render(request, "vertrieb/edit_angebot.html", {"form_angebot": form_angebot})


class VertriebAutoFieldView(View, VertriebCheckMixin):
    data = []

    def get(self, request, *args, **kwargs):
        profile, created = User.objects.get_or_create(zoho_id=request.user.zoho_id)
        self.data = json.loads(profile.zoho_data_text)
        try:
            self.data != []
            name = request.GET.get("name", None)
            data = next((item for item in self.data if item["name"] == name), None)

            return JsonResponse(data)
        except:
            name = request.GET.get("name", None)
            data = next((item for item in self.data if item["name"] == name), None)

            if data is None:
                data = {}
            return JsonResponse(data)


def map_view(request, angebot_id, *args, **kwargs):
    vertrieb_angebot = VertriebAngebot.objects.get(
        angebot_id=angebot_id, user=request.user
    )

    context = {
        "LATITUDE": vertrieb_angebot.postanschrift_latitude,
        "LONGITUDE": vertrieb_angebot.postanschrift_longitude,
    }
    return render(request, "vertrieb/extra/map.html", context)


class AngebotEditView(LoginRequiredMixin, VertriebCheckMixin, FormMixin, View):
    model = VertriebAngebot
    form_class = VertriebAngebotForm
    template_name = "vertrieb/edit_angebot.html"
    context_object_name = "vertrieb_angebot"

    def _log_and_notify_attempt(self, user, action_type):
        if TELEGRAM_LOGGING:
            try:
                log_and_notify(f"{user.email}: Attempt to {action_type}")
            except Exception:
                pass

    def _log_and_notify_success(self, user):
        if TELEGRAM_LOGGING:
            try:
                log_and_notify(f"{user.email} Successful!")
            except Exception:
                pass

    def _log_and_notify_error(self, user, form):
        if TELEGRAM_LOGGING:
            try:
                # Formatting the error message for clarity
                formatted_errors = "\n".join(
                    [
                        f"*{field.replace('_', ' ').capitalize()}*: {error}"
                        for field, errors in form.errors.items()
                        for error in errors
                    ]
                )
                message = f"*Error for {user.email}*\n{formatted_errors}"
                log_and_notify(message)
            except Exception as e:
                # Log the exception for debugging purposes
                log_and_notify(f"Error logging to Telegram: {str(e)}")

    def dispatch(self, request, *args, **kwargs):
        angebot_id = kwargs.get("angebot_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        self.fetch_angebot_data(request, angebot_id, request.user)
        self.handle_status_change(angebot_id)

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(self.model, angebot_id=self.kwargs.get("angebot_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vertrieb_angebot = self.get_object()

        user_profile = (
            self.request.user
        )  # assuming a profile model is linked to the user

        context["form"] = self.form_class(
            instance=vertrieb_angebot,
            user=self.request.user,
        )
        # context["form_rechner"] = VertriebAngebotRechnerForm(
        #     instance=vertrieb_angebot, user=self.request.user
        # )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def handle_status_change(self, angebot_id):
        for angebot in VertriebAngebot.objects.filter(
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

    def fetch_angebot_data(self, request, angebot_id, user):
        fetched_angebote_list = []
        vertrieb_angebot = VertriebAngebot.objects.get(
            angebot_id=angebot_id, user=request.user
        )
        zoho_id = vertrieb_angebot.zoho_id
        if zoho_id is not None:
            item = fetch_angenommen_status(request, zoho_id)
            fetched_data = {
                "zoho_id": item.get("ID", ""),
                "status": item.get("Status", ""),
                "status_pva": item.get("Status_PVA", ""),
                "angebot_bekommen_am": item.get("Angebot_bekommen_am", ""),
                "anrede": item.get("Name", {}).get("prefix", ""),
                "strasse": item.get("Adresse_PVA", {}).get("address_line_1", ""),
                "ort": item.get("Adresse_PVA", {}).get("postal_code", "")
                + " "
                + item.get("Adresse_PVA", {}).get("district_city", ""),
                "postanschrift_longitude": item.get("Adresse_PVA", {}).get(
                    "longitude", ""
                ),
                "postanschrift_latitude": item.get("Adresse_PVA", {}).get(
                    "latitude", ""
                ),
                "telefon_festnetz": item.get("Telefon_Festnetz", ""),
                "telefon_mobil": item.get("Telefon_mobil", ""),
                # "zoho_kundennumer": kundennumer,
                "email": item.get("Email", ""),
                "notizen": item.get("Notizen", ""),
                "name": item.get("Name", {}).get("last_name", "")
                + " "
                + item.get("Name", {}).get("suffix", "")
                + " "
                + item.get("Name", {}).get("first_name", ""),
                "vertriebler_display_value": item.get("Vertriebler", {}).get(
                    "display_value", ""
                ),
                "vertriebler_id": item.get("Vertriebler", {}).get("ID", ""),
                "adresse_pva_display_value": item.get("Adresse_PVA", {}).get(
                    "display_value", ""
                ),
                "anfrage_vom": item.get("Anfrage_vom", ""),
            }
            vertrieb_angebot.ag_fetched_data = json.dumps(fetched_data)
            vertrieb_angebot.save()
        else:
            pass

    def get(self, request, angebot_id, *args, **kwargs):
        vertrieb_angebot = VertriebAngebot.objects.get(
            angebot_id=angebot_id, user=request.user
        )
        zoho_id = vertrieb_angebot.zoho_id
        user = request.user

        if zoho_id is not None:
            item = json.loads(vertrieb_angebot.ag_fetched_data)

            data = json.loads(user.zoho_data_text or '[["test", "test"]]')
            name_to_kundennumer = {
                item["name"]: item["zoho_kundennumer"] for item in data
            }

            name = vertrieb_angebot.name
            zoho_id = vertrieb_angebot.zoho_id
            kundennumer = name_to_kundennumer[name]

            vertrieb_angebot.vorname_nachname = vertrieb_angebot.name
            vertrieb_angebot.anfrage_ber = item.get("anfrage_vom")
            vertrieb_angebot.status_pva = item.get("status_pva")
            vertrieb_angebot.angebot_bekommen_am = (
                item.get("angebot_bekommen_am")
                if item.get("angebot_bekommen_am")
                else ""
            )
            vertrieb_angebot.leadstatus = (
                item.get("leadstatus") if item.get("leadstatus") else ""
            )
            vertrieb_angebot.notizen = item.get("notizen")
            vertrieb_angebot.email = item.get("email")
            vertrieb_angebot.zoho_kundennumer = kundennumer
            vertrieb_angebot.postanschrift_latitude = item.get("postanschrift_latitude")
            vertrieb_angebot.postanschrift_longitude = item.get(
                "postanschrift_longitude"
            )
            vertrieb_angebot.empfohlen_von = item.get("empfohlen_von")
            vertrieb_angebot.termine_text = item.get("termine_text")
            vertrieb_angebot.termine_id = item.get("termine_id")
            vertrieb_angebot.save()
            form = self.form_class(instance=vertrieb_angebot, user=request.user)  # type: ignore
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
            countdown = vertrieb_angebot.countdown()
            context = {
                "countdown": vertrieb_angebot.countdown(),
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
        else:
            form = self.form_class(instance=vertrieb_angebot, user=request.user)  # type: ignore
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
            countdown = vertrieb_angebot.countdown()
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
            VertriebAngebot, angebot_id=self.kwargs.get("angebot_id")
        )
        user = request.user
        user_zoho_id = user.zoho_id
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)

        if request.method == "POST":
            action_type = request.POST.get("action_type")
            if action_type == "switch_to_bekommen":
                # self._log_and_notify_attempt(user, action_type)

                if form.is_valid():
                    instance = form.instance
                    vertrieb_angebot.angebot_id_assigned = True
                    profile, created = User.objects.get_or_create(
                        zoho_id=request.user.zoho_id
                    )

                    data_loads = json.loads(profile.zoho_data_text)
                    name = instance.name

                    data = next(
                        (item for item in data_loads if item["name"] == name), None
                    )
                    instance.zoho_kundennumer = data.get("zoho_kundennumer")
                    vertrieb_angebot.save()
                    form.instance.status = "bekommen"
                    form.save()
                    response = pushAngebot(vertrieb_angebot, user_zoho_id)
                    response_data = response.json()
                    new_record_id = response_data["data"]["ID"]
                    vertrieb_angebot.angebot_zoho_id = new_record_id
                    vertrieb_angebot.save()

                    # self._log_and_notify_success(user)
                    if TELEGRAM_LOGGING:
                        send_message_to_bot(
                            f"{user.first_name} {user.last_name} hat ein PDF Angebot für einen Kunden erstellt. Kunde: {vertrieb_angebot.vorname_nachname}"
                        )
                    return redirect(
                        "vertrieb_interface:create_angebot_pdf_user",
                        vertrieb_angebot.angebot_id,
                    )
            elif action_type == "switch_to_bekommen_pdf_plus_kalk":
                # self._log_and_notify_attempt(user, action_type)

                if form.is_valid():
                    vertrieb_angebot.angebot_id_assigned = True
                    instance = form.instance
                    profile, created = User.objects.get_or_create(
                        zoho_id=request.user.zoho_id
                    )

                    data_loads = json.loads(profile.zoho_data_text)
                    name = instance.name

                    data = next(
                        (item for item in data_loads if item["name"] == name), None
                    )
                    instance.zoho_kundennumer = data.get("zoho_kundennumer")
                    instance.save()

                    vertrieb_angebot.save()
                    form.instance.status = "bekommen"
                    form.save()
                    response = pushAngebot(vertrieb_angebot, user_zoho_id)
                    response_data = response.json()
                    new_record_id = response_data["data"]["ID"]
                    vertrieb_angebot.angebot_zoho_id = new_record_id
                    vertrieb_angebot.save()
                    # self._log_and_notify_success(user)
                    if TELEGRAM_LOGGING:
                        send_custom_message(
                            user,
                            "hat ein PDF Angebot für einen Interessenten erstellt.",
                            f"Kunde: {vertrieb_angebot.vorname_nachname} 📑",
                        )
                    return redirect(
                        "vertrieb_interface:create_angebot_and_calc_pdf",
                        vertrieb_angebot.angebot_id,
                    )
            elif action_type == "zahlungs":
                # self._log_and_notify_attempt(user, action_type)
                if form.is_valid():
                    instance = form.instance
                    instance.zahlungsbedingungen = form.cleaned_data[
                        "zahlungsbedingungen"
                    ]
                    instance.save(update_fields=["zahlungsbedingungen"])
                    # self._log_and_notify_success(user)
                    return redirect(
                        "vertrieb_interface:create_angebot_pdf_user",
                        vertrieb_angebot.angebot_id,
                    )
            elif action_type == "kalkulation_erstellen":
                # self._log_and_notify_attempt(user, action_type)
                if form.is_valid():
                    instance = form.instance
                    instance.save()
                    # self._log_and_notify_success(user)
                    return redirect(
                        "vertrieb_interface:create_calc_pdf",
                        vertrieb_angebot.angebot_id,
                    )
            elif action_type == "angebotsumme_rechnen":
                # self._log_and_notify_attempt(user, action_type)
                if form.is_valid():
                    instance = form.instance
                    instance.angebot_id_assigned = False
                    data = json.loads(user.zoho_data_text or '[["test", "test"]]')
                    name_to_kundennumer = {
                        item["name"]: item["zoho_kundennumer"] for item in data
                    }
                    name_to_zoho_id = {item["name"]: item["zoho_id"] for item in data}
                    name = form.cleaned_data["name"]
                    kundennumer = name_to_kundennumer[name]
                    instance.zoho_kundennumer = kundennumer
                    vertrieb_angebot.save()
                    form.save()

                    # self._log_and_notify_success(user)
                    return redirect(
                        "vertrieb_interface:edit_angebot",
                        vertrieb_angebot.angebot_id,
                    )

            elif action_type == "save":

                if form.is_valid():
                    instance = form.instance
                    instance.angebot_id_assigned = True
                    
                    name = instance.name
                    data = json.loads(user.zoho_data_text or '[["test", "test"]]')
                    name_to_kundennumer = {
                        item["name"]: item["zoho_kundennumer"] for item in data
                    }
                    name_to_zoho_id = {item["name"]: item["zoho_id"] for item in data}
                    name = form.cleaned_data["name"]
                    kundennumer = name_to_kundennumer[name]
                    instance.zoho_kundennumer = kundennumer
                    angebot_existing = VertriebAngebot.objects.filter(
                        user=user,
                        angebot_id_assigned=True,
                        status="",
                        zoho_kundennumer=kundennumer,
                    )

                    if angebot_existing.count() != 0:
                        extracted_part = (
                            str(angebot_existing)
                            .split("VertriebAngebot: ")[1]
                            .split(">]")[0]
                        )
                        # Add a message indicating that there are duplicate instances
                        form.add_error(
                            None,
                            f"Sie können dieses Angebot nicht speichern, da Sie in Ihrer Liste bereits ein Angebot {extracted_part}  mit einem leeren Status für diesen Interessenten haben.\nEntweder Sie schließen die Erstellung des Angebots ab, indem Sie ein PDF-Dokument erstellen.\nOder löschen Sie es.\n",
                        )
                        return self.form_invalid(form, vertrieb_angebot, request)

                    else:
                        instance.save()
                        form.save()
                        put_form_data_to_zoho_jpp(form)
                        all_user_angebots_list = fetch_user_angebote_all(request)
                        user.zoho_data_text = json.dumps(all_user_angebots_list)
                        user.save()
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

    def form_invalid(self, form, vertrieb_angebot, request, *args, **kwargs):
        context = self.get_context_data()
        countdown = vertrieb_angebot.countdown()
        context["status_change_field"] = vertrieb_angebot.status_change_field
        context["countdown"] = vertrieb_angebot.countdown()
        context["messages"] = messages.get_messages(request)
        context["vertrieb_angebot"] = vertrieb_angebot
        context["form"] = form
        return render(self.request, self.template_name, context)

    def load_data_from_zoho_to_angebot_id(self, request):
        pass


class TicketEditView(LoginRequiredMixin, VertriebCheckMixin, FormMixin, View):
    model = VertriebAngebot
    form_class = TicketForm
    template_name = "vertrieb/edit_ticket.html"
    context_object_name = "vertrieb_angebot"

    def dispatch(self, request, *args, **kwargs):
        angebot_id = kwargs.get("angebot_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(self.model, angebot_id=self.kwargs.get("angebot_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vertrieb_angebot = self.get_object()

        context["form"] = self.form_class(  # type: ignore
            instance=vertrieb_angebot, user=self.request.user  # type: ignore
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
        zoho_id = vertrieb_angebot.zoho_id

        vertrieb_angebot.vorname_nachname = vertrieb_angebot.name

        form = self.form_class(instance=vertrieb_angebot, user=request.user)  # type: ignore
        user = request.user
        # if TELEGRAM_LOGGING:
        #     send_message_to_bot(
        #         f"{user.email}: Attempt to create Ticket {vertrieb_angebot.angebot_id}:"
        #     )
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
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)  # type: ignore
        if "pdf_erstellen" in request.POST:
            if form.is_valid():
                vertrieb_angebot.angebot_id_assigned = True

                data = json.loads(user.zoho_data_text or '[["test", "test"]]')
                name_to_kundennumer = {
                    item["name"]: item["zoho_kundennumer"] for item in data
                }
                name_to_zoho_id = {item["name"]: item["zoho_id"] for item in data}
                name = form.cleaned_data["name"]

                kundennumer = name_to_kundennumer[name]

                zoho_id = name_to_zoho_id[name]

                vertrieb_angebot.zoho_kundennumer = kundennumer
                vertrieb_angebot.zoho_id = int(zoho_id)
                vertrieb_angebot.save()
                form.save()  # type:ignore
                if TELEGRAM_LOGGING:
                    send_custom_message(
                        user,
                        "hat ein PDF Ticket für einen Kunden erstellt.",
                        f"Kunde: {vertrieb_angebot.vorname_nachname} 🎟️",
                    )

                return redirect(
                    "vertrieb_interface:create_ticket_pdf", vertrieb_angebot.angebot_id
                )
        elif form.is_valid():
            instance = form.instance
            data = json.loads(user.zoho_data_text or '[["test", "test"]]')
            name_to_kundennumer = {
                item["name"]: item["zoho_kundennumer"] for item in data
            }
            name_to_zoho_id = {item["name"]: item["zoho_id"] for item in data}
            name = form.cleaned_data["name"]
            kundennumer = name_to_kundennumer[name]
            zoho_id = name_to_zoho_id[name]
            vertrieb_angebot.zoho_kundennumer = kundennumer
            vertrieb_angebot.zoho_id = int(zoho_id)
            vertrieb_angebot.save()
            instance.save()

            return redirect(
                "vertrieb_interface:edit_ticket", vertrieb_angebot.angebot_id
            )
        return self.form_invalid(form, vertrieb_angebot)

    def form_invalid(self, form, vertrieb_angebot, *args, **kwargs):
        context = self.get_context_data()

        context["status_change_field"] = vertrieb_angebot.status_change_field

        context["vertrieb_angebot"] = vertrieb_angebot
        context["form"] = form

        return render(self.request, self.template_name, context)

    def load_data_from_zoho_to_angebot_id(self, request):
        pass


class KalkulationEditView(LoginRequiredMixin, VertriebCheckMixin, FormMixin, View):
    model = VertriebAngebot
    form_class = VertriebAngebotForm
    template_name = "vertrieb/edit_calc.html"
    context_object_name = "vertrieb_angebot"

    def dispatch(self, request, *args, **kwargs):
        angebot_id = kwargs.get("angebot_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(self.model, angebot_id=self.kwargs.get("angebot_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vertrieb_angebot = self.get_object()

        context["form"] = self.form_class(  # type: ignore
            instance=vertrieb_angebot, user=self.request.user  # type: ignore
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
        zoho_id = vertrieb_angebot.zoho_id

        vertrieb_angebot.vorname_nachname = vertrieb_angebot.name

        form = self.form_class(instance=vertrieb_angebot, user=request.user)  # type: ignore
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
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)  # type: ignore
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
                        f"Kunde: {vertrieb_angebot.vorname_nachname} 📊",
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

    def load_data_from_zoho_to_angebot_id(self, request):
        pass


class DeleteAngebot(DeleteView):
    model = VertriebAngebot
    template_name = "view_admin_orders.html"

    def get_success_url(self):
        return reverse("vertrieb_interface:view_admin_orders")

    def get_object(self, queryset=None):
        return VertriebAngebot.objects.get(angebot_id=self.kwargs["angebot_id"])

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        CustomLogEntry.objects.log_action(
            user_id=self.object.user_id,
            content_type_id=ContentType.objects.get_for_model(self.object).pk,
            object_id=self.object.pk,
            object_repr=str(self.object),
            action_flag=CHANGE,
            status=self.object.status,
        )
        self.object.delete()
        return redirect(self.get_success_url())


class DeleteUserAngebot(DeleteView):
    model = VertriebAngebot
    template_name = "vertrieb/view_orders.html"

    def get_success_url(self):
        return reverse("vertrieb_interface:view_orders")

    def get_object(self, queryset=None):
        return VertriebAngebot.objects.get(angebot_id=self.kwargs["angebot_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if TELEGRAM_LOGGING:
            send_custom_message(
                self.request.user, "Accessed the offers list page.", "Info"
            )
        return context

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return response

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.angebot_id_assigned = False
        self.object.save()
        CustomLogEntry.objects.log_action(
            user_id=self.object.user_id,
            content_type_id=ContentType.objects.get_for_model(self.object).pk,
            object_id=self.object.pk,
            object_repr=str(self.object),
            action_flag=CHANGE,
            status=self.object.status,
        )
        self.object.delete()
        return redirect(self.get_success_url())


class ViewOrders(LoginRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/view_orders.html"
    context_object_name = "angebots"

    def get_queryset(self):
        # Optimized query to directly exclude "angenommen" and "bekommen" statuses
        return self.model.objects.filter(user=self.request.user).exclude(
            status__in=["angenommen", "bekommen"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if TELEGRAM_LOGGING:
            send_custom_message(
                self.request.user, "Accessed the offers list page.", "Info"
            )
        return context


def set_angebot_id_assigned_false_for_user(request):
    user = request.user
    angenommen_angebots = VertriebAngebot.objects.filter(user=user, status="angenommen")

    for angebot in angenommen_angebots:
        other_angebots = VertriebAngebot.objects.filter(
            user=user, zoho_kundennumer=angebot.zoho_kundennumer
        ).exclude(status="angenommen")

        for other_angebot in other_angebots:
            other_angebot.angebot_id_assigned = False
            other_angebot.save()


def process_vertrieb_angebot(request):
    user = request.user
    bek_ang_list = []
    angenommen_angebote = VertriebAngebot.objects.filter(user=user, status="angenommen")
    for angebot in angenommen_angebote:
        zoho_kundennumer = angebot.zoho_kundennumer
        bekommen_angebote = VertriebAngebot.objects.filter(
            zoho_kundennumer=zoho_kundennumer, status="bekommen"
        )
        bek_ang_list.append(bekommen_angebote)

    for queryset in bek_ang_list:
        for bekommen_angebot in queryset:
            angebot_zoho_id = bekommen_angebot.angebot_zoho_id

            if angebot_zoho_id is not None:
                # send_message_to_bot(f"{bekommen_angebot.angebot_zoho_id}")
                delete_redundant_angebot(angebot_zoho_id)
                bekommen_angebot.angebot_id_assigned = False
                bekommen_angebot.save()
            else:
                pass


def update_status_to_angenommen(angebot_ids):
    # Filter VertriebAngebot instances with the given list of angebot_id values
    angebote = VertriebAngebot.objects.filter(angebot_id__in=angebot_ids)

    # Update status to 'angenommen' for the filtered instances
    angebote.update(status="angenommen")

    # Optionally, you can return the count of updated instances
    return angebote.count()


def update_vertrieb_angebot_assignment(user):
    user_data = json.loads(user.zoho_data_text)
    # Extract zoho_id values from user_data
    if user_data != []:
        user_zoho_ids = {item["zoho_id"] for item in user_data}

        # Filter vertrieb_angebot instances that need to be updated
        vertrieb_angebots_to_update = VertriebAngebot.objects.filter(
            user=user, angebot_id_assigned=True
        ).exclude(zoho_id__in=user_zoho_ids)

        # Bulk update angebot_id_assigned to False
        vertrieb_angebots_to_update.update(angebot_id_assigned=False)

    else:
        pass


@user_passes_test(vertrieb_check)
def load_user_angebots(request):
    existing_angebot_ids = extract_values(request)
    user = request.user

    try:
        profile, created = User.objects.update_or_create(zoho_id=request.user.zoho_id)
        user = get_object_or_404(User, zoho_id=request.user.zoho_id)
        kurz = user.kuerzel  # type: ignore

        all_user_angebots_list = fetch_user_angebote_all(request)
        profile.zoho_data_text = json.dumps(all_user_angebots_list)
        profile.save()
        user_data = json.loads(user.zoho_data_text or '[["test", "test"]]')
        # Extract zoho_id values from user_data
        if user_data != []:
            user_zoho_ids = {item["zoho_id"] for item in user_data}

            zoho_id_to_status_pva = {
                item["zoho_id"]: item["status_pva"] for item in user_data
            }
        for existing_angebot_id in existing_angebot_ids:
            vertrieb_angebot, created = VertriebAngebot.objects.get_or_create(
                user=user, angebot_id=existing_angebot_id
            )
            zoho_id = vertrieb_angebot.zoho_id
            if zoho_id != None:
                status_pva = zoho_id_to_status_pva[zoho_id]
                vertrieb_angebot.status_pva = status_pva
                vertrieb_angebot.save()

        update_vertrieb_angebot_assignment(user)
        update_status_to_angenommen(existing_angebot_ids)
        process_vertrieb_angebot(request)

        # if TELEGRAM_LOGGING:
        #     send_message_to_bot(f"{user.email}: Aufträge aus JPP aktualisiert")
        return JsonResponse({"status": "success"}, status=200)
    except Exception:
        return JsonResponse(
            {"status": "failed", "error": "Not a POST request."}, status=400
        )


def replace_spaces_with_underscores(s: str) -> str:
    return s.replace(" ", "_")


@admin_required
def create_angebot_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = vertrieb_angebot.user
    data = vertrieb_angebot.data
    name = replace_spaces_with_underscores(vertrieb_angebot.name)
    if vertrieb_angebot.angebot_pdf_admin is None:
        pdf_content = angebot_pdf_creator.createOfferPdf(data, vertrieb_angebot, user)
        vertrieb_angebot.angebot_pdf_admin = pdf_content
        vertrieb_angebot.save()
    async_iterator = AsyncBytesIter(vertrieb_angebot.angebot_pdf_admin)
    response = StreamingHttpResponse(async_iterator, content_type="application/pdf")
    response["Content-Disposition"] = (
        f"inline; filename={name}_{vertrieb_angebot.angebot_id}.pdf"
    )
    return response


@login_required
def create_angebot_pdf_user(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data
    certifikate = user.user_certifikate

    pdf_content = angebot_pdf_creator_user.createOfferPdf(
        data,
        vertrieb_angebot,
        certifikate,
        user,
    )
    vertrieb_angebot.angebot_pdf = pdf_content
    vertrieb_angebot.save()

    return redirect("vertrieb_interface:document_view", angebot_id=angebot_id)


@login_required
def create_angebot_and_calc_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data
    certifikate = user.user_certifikate

    pdf_content = angebot_plus_calc_pdf.createOfferPdf(
        data,
        vertrieb_angebot,
        certifikate,
        user,
    )
    vertrieb_angebot.angebot_and_calc_pdf = pdf_content
    vertrieb_angebot.save()

    return redirect("vertrieb_interface:document_and_calc_view", angebot_id=angebot_id)


@login_required
def create_calc_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data
    name = replace_spaces_with_underscores(vertrieb_angebot.name)

    pdf_content = calc_pdf_creator.createCalcPdf2(
        data,
        vertrieb_angebot,
        user,
    )
    vertrieb_angebot.calc_pdf = pdf_content
    vertrieb_angebot.save()

    pdf_link = os.path.join(settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Kalkulationen/Kalkulation_{name}_{vertrieb_angebot.angebot_id}.pdf")  # type: ignore

    return redirect("vertrieb_interface:document_calc_view", angebot_id=angebot_id)


@login_required
def create_ticket_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data
    name = replace_spaces_with_underscores(vertrieb_angebot.name)

    pdf_content = ticket_pdf_creator.createTicketPdf(data)
    vertrieb_angebot.ticket_pdf = pdf_content
    vertrieb_angebot.save()
    return redirect("vertrieb_interface:document_ticket_view", angebot_id=angebot_id)


class DocumentView(LoginRequiredMixin, DetailView):
    model = VertriebAngebot
    template_name = "vertrieb/document_view.html"
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
        pdf_url = reverse("vertrieb_interface:serve_pdf", args=[angebot_id])
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
                return redirect(
                    "vertrieb_interface:document_view", form.instance.angebot_id
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
        file_data = (
            vertrieb_angebot.angebot_pdf.tobytes()
        )  # Ensure this is the correct way to get PDF data
        name = replace_spaces_with_underscores(vertrieb_angebot.name)
        email.attach(
            f"{name}_{vertrieb_angebot.angebot_id}.pdf", file_data, "application/pdf"
        )

        if vertrieb_angebot.datenblatter_solar_module:
            if (
                vertrieb_angebot.solar_module
                == "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B"
            ):
                self._attach_datenblatter(
                    email,
                    datenblatter,
                    [
                        "solar_module_1",
                    ],
                )
            if (
                vertrieb_angebot.solar_module
                == "Jinko Solar Tiger Neo N-type JKM425N-54HL4-(V)"
            ):
                self._attach_datenblatter(
                    email,
                    datenblatter,
                    [
                        "solar_module_2",
                    ],
                )
            if (
                vertrieb_angebot.solar_module == "Phono Solar PS420M7GFH-18/VNH"
                or vertrieb_angebot.solar_module == "Phono Solar PS430M8GFH-18/VNH"
                or vertrieb_angebot.solar_module == "Phono Solar PS430M8GFH-18/VSH"
            ):
                self._attach_datenblatter(email, datenblatter, ["solar_module_3"])
        
        if vertrieb_angebot.datenblatter_optimizer:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, ["optimizer"])
            else:
                self._attach_datenblatter(email, datenblatter, ["optimizer_viessmann"])
                self._attach_datenblatter(email, datenblatter, ["viessmann_tigo"])

        if vertrieb_angebot.datenblatter_speichermodule:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, ["speicher_module"])
            else:
                self._attach_datenblatter(email, datenblatter, ["speicher_module_viessmann"])

        if vertrieb_angebot.datenblatter_wechselrichter:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, ["wechselrichter"])

        if vertrieb_angebot.datenblatter_wallbox:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, ["wall_box"])

        if vertrieb_angebot.datenblatter_backup_box:
            if vertrieb_angebot.hersteller == "Huawei":
                self._attach_datenblatter(email, datenblatter, ["backup_box"])

        if vertrieb_angebot.hersteller == "Viessmann":
            self._attach_datenblatter(email, datenblatter, ["viessmann_allgemeine_bedingungen"])
            self._attach_datenblatter(email, datenblatter, ["viessmann_versicherung_ausweis"])



    def _attach_datenblatter(self, email, datenblatter, fields):
        for field in fields:
            datenblatt = getattr(datenblatter, field, None)
            if datenblatt:
                with datenblatt.open("rb") as file:
                    file_data = file.read()
                email.attach(f"{field}.pdf", file_data, "application/pdf")

    def form_invalid(self, form):
        return render(
            self.request, self.template_name, self.get_context_data(form=form)
        )


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
            "vertrieb_interface:serve_angebot_and_calc_pdf", args=[angebot_id]
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
        email_sent = False
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
        file_data = (
            vertrieb_angebot.angebot_and_calc_pdf.tobytes()
        )  # Ensure this is the correct way to get PDF data
        name = replace_spaces_with_underscores(vertrieb_angebot.name)
        email.attach(
            f"{name}_{vertrieb_angebot.angebot_id}.pdf", file_data, "application/pdf"
        )

        if vertrieb_angebot.datenblatter_solar_module:
            if (
                vertrieb_angebot.solar_module
                == "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B"
            ):
                self._attach_datenblatter(
                    email,
                    datenblatter,
                    [
                        "solar_module_1",
                    ],
                )
            if (
                vertrieb_angebot.solar_module
                == "Jinko Solar Tiger Neo N-type JKM425N-54HL4-(V)"
            ):
                self._attach_datenblatter(
                    email,
                    datenblatter,
                    [
                        "solar_module_2",
                    ],
                )
            if (
                vertrieb_angebot.solar_module == "Phono Solar PS420M7GFH-18/VNH"
                or "Phono Solar PS430M8GFH-18/VSH"
            ):
                self._attach_datenblatter(email, datenblatter, ["solar_module_3"])

        if vertrieb_angebot.datenblatter_speichermodule:
            self._attach_datenblatter(email, datenblatter, ["speicher_module"])

        if vertrieb_angebot.datenblatter_wechselrichter:
            self._attach_datenblatter(email, datenblatter, ["wechselrichter"])

        if vertrieb_angebot.datenblatter_wallbox:
            self._attach_datenblatter(email, datenblatter, ["wall_box"])

        if vertrieb_angebot.datenblatter_backup_box:
            self._attach_datenblatter(email, datenblatter, ["backup_box"])

    def _attach_datenblatter(self, email, datenblatter, fields):
        for field in fields:
            datenblatt = getattr(datenblatter, field, None)
            if datenblatt:
                with datenblatt.open("rb") as file:
                    file_data = file.read()
                email.attach(f"{field}.pdf", file_data, "application/pdf")

    def form_invalid(self, form):
        return render(
            self.request, self.template_name, self.get_context_data(form=form)
        )


@login_required
def document_calc_view(request, angebot_id):
    pdf_url = reverse("vertrieb_interface:serve_calc_pdf", args=[angebot_id])
    context = {"pdf_url": pdf_url, "angebot_id": angebot_id}
    return render(request, "vertrieb/document_calc_view.html", context)


@login_required
def document_ticket_view(request, angebot_id):
    pdf_url = reverse("vertrieb_interface:serve_ticket_pdf", args=[angebot_id])
    context = {"pdf_url": pdf_url, "angebot_id": angebot_id}
    return render(request, "vertrieb/document_ticket_view.html", context)


@login_required
def serve_pdf(request, angebot_id):
    decoded_angebot_id = unquote(angebot_id)
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=decoded_angebot_id)
    name = replace_spaces_with_underscores(vertrieb_angebot.name)
    filename = f"{name}_{vertrieb_angebot.angebot_id}.pdf"
    sleep(0.5)

    if not vertrieb_angebot.angebot_pdf:
        return StreamingHttpResponse("File not found.", status=404)

    async_iterator = AsyncFileIter(vertrieb_angebot.angebot_pdf)

    response = StreamingHttpResponse(async_iterator, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


@login_required
def serve_angebot_and_calc_pdf(request, angebot_id):
    decoded_angebot_id = unquote(angebot_id)
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=decoded_angebot_id)
    name = replace_spaces_with_underscores(vertrieb_angebot.name)
    filename = f"{name}_{vertrieb_angebot.angebot_id}.pdf"
    sleep(0.5)

    if not vertrieb_angebot.angebot_and_calc_pdf:
        return StreamingHttpResponse("File not found.", status=404)

    async_iterator = AsyncFileIter(vertrieb_angebot.angebot_and_calc_pdf)

    response = StreamingHttpResponse(async_iterator, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


@login_required
def serve_calc_pdf(request, angebot_id):
    decoded_angebot_id = unquote(angebot_id)
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=decoded_angebot_id)
    name = replace_spaces_with_underscores(vertrieb_angebot.name)
    filename = f"Kalkulation_{name}_{vertrieb_angebot.angebot_id}.pdf"
    sleep(0.5)
    if not vertrieb_angebot.calc_pdf:
        return StreamingHttpResponse("File not found.", status=404)

    # Create an instance of AsyncFileIter with the file object
    async_iterator = AsyncFileIter(vertrieb_angebot.calc_pdf)

    response = StreamingHttpResponse(async_iterator, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


@login_required
def serve_ticket_pdf(request, angebot_id):
    decoded_angebot_id = unquote(angebot_id)
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=decoded_angebot_id)
    name = replace_spaces_with_underscores(vertrieb_angebot.name)
    filename = f"Ticket_{name}_{vertrieb_angebot.angebot_id}.pdf"
    sleep(0.5)
    if not vertrieb_angebot.ticket_pdf:
        return StreamingHttpResponse("File not found.", status=404)

    # Create an instance of AsyncFileIter with the file object
    async_iterator = AsyncFileIter(vertrieb_angebot.ticket_pdf)

    response = StreamingHttpResponse(async_iterator, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


@login_required
def serve_dokumentation(request):
    filename = os.path.join(settings.STATIC_ROOT, "dokumentation_angebotstool.pdf")
    try:
        return FileResponse(open(filename, "rb"), content_type="application/pdf")
    except FileNotFoundError:
        return HttpResponse("File not found.", status=404)


@login_required
def documentation_view(request):
    return render(request, "vertrieb/documentation_view.html")


@login_required
def send_support_message(request):
    if request.method == "POST":
        user = request.user

        subject = f"AngebotsTool Support Request from {user.first_name, user.last_name}"
        body = "I need help, please contact me!"

        connection = get_connection(
            backend=EMAIL_BACKEND,
            host=user.smtp_server,
            port=user.smtp_port,
            username=user.smtp_username,
            password=user.smtp_password,
            use_tsl=True,
            fail_silently=False,
        )
        email = EmailMultiAlternatives(
            subject,
            body,
            user.smtp_username,
            ["si@juno-solar.com"],
            connection=connection,
        )
        try:
            email.send()
            messages.success(request, "Email sent successfully")

        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")

        return JsonResponse({"status": "success"}, status=200)

    else:
        return JsonResponse(
            {"status": "failed", "error": "Not a POST request."}, status=400
        )


@login_required
def send_invoice(request, angebot_id):
    if request.method == "POST":
        user = request.user
        data = json.loads(request.body)
        empfanger_email = data.get("email")

        vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
        text_for_email = data.get("text_for_email")
        pdf = vertrieb_angebot.angebot_pdf
        subject = f"Angebot Photovoltaikanlage {angebot_id}"
        # geerter = f"Sehr geehrter {vertrieb_angebot.vorname_nachname}\n\n"
        body = text_for_email
        name = replace_spaces_with_underscores(vertrieb_angebot.name)
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print(f"From: {user.smtp_username}")
        print(f"To: si@juno-solar.com")
        print(empfanger_email)

        connection = get_connection(
            backend=EMAIL_BACKEND,
            host=user.smtp_server,
            port=user.smtp_port,
            username=user.smtp_username,
            password=user.smtp_password,
            use_tsl=True,
            fail_silently=False,
        )
        email = EmailMultiAlternatives(
            subject,
            body,
            user.smtp_username,
            [f"{empfanger_email}"],
            connection=connection,
        )
        file_data = vertrieb_angebot.angebot_pdf.tobytes()  # type:ignore
        email.attach(
            f"{name}_{vertrieb_angebot.angebot_id}.pdf", file_data, "application/pdf"
        )

        try:
            email.send()
            print("Email sent successfully")
            messages.success(request, "Email sent successfully")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            messages.error(request, f"Failed to send email: {str(e)}")
        return JsonResponse({"status": "success"}, status=200)
    else:
        print("Not a POST request")
        return JsonResponse(
            {"status": "failed", "error": "Not a POST request."}, status=400
        )


@login_required
def send_calc_invoice(request, angebot_id):
    if request.method == "POST":
        user = request.user

        vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
        pdf = vertrieb_angebot.calc_pdf

        subject = f"Kalkulation Photovoltaikanlage {angebot_id}"
        geerter = f"Sehr geehrter {vertrieb_angebot.vorname_nachname}\n\n"
        body = geerter + user.smtp_body
        name = replace_spaces_with_underscores(vertrieb_angebot.name)
        connection = get_connection(
            backend=EMAIL_BACKEND,
            host=user.smtp_server,
            port=user.smtp_port,
            username=user.smtp_username,
            password=user.smtp_password,
            use_tsl=True,
            fail_silently=False,
        )

        email = EmailMultiAlternatives(
            subject,
            body,
            user.smtp_username,
            [f"{vertrieb_angebot.email}"],
            connection=connection,
        )

        file_data = pdf.tobytes()  # type:ignore
        email.attach(
            f"Kalkulation_{name}_{vertrieb_angebot.angebot_id}.pdf",
            file_data,
            "application/pdf",
        )

        try:
            email.send()
            messages.success(request, "Email sent successfully")

        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")

        return JsonResponse({"status": "success"}, status=200)

    else:
        return JsonResponse(
            {"status": "failed", "error": "Not a POST request."}, status=400
        )


@login_required
def send_ticket_invoice(request, angebot_id):
    if request.method == "POST":
        user = request.user

        vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
        pdf = vertrieb_angebot.ticket_pdf
        subject = f"Ticket Photovoltaikanlage {angebot_id}"
        geerter = f"Sehr geehrter {vertrieb_angebot.vorname_nachname}\n\n"
        body = geerter + user.smtp_body
        name = replace_spaces_with_underscores(vertrieb_angebot.name)
        connection = get_connection(
            backend=EMAIL_BACKEND,
            host=user.smtp_server,
            port=user.smtp_port,
            username=user.smtp_username,
            password=user.smtp_password,
            use_tsl=True,
            fail_silently=False,
        )

        email = EmailMultiAlternatives(
            subject,
            body,
            user.smtp_username,
            [f"{vertrieb_angebot.email}"],
            connection=connection,
        )

        file_data = pdf.tobytes()  # type:ignore
        email.attach(
            f"Ticket_{name}_{vertrieb_angebot.angebot_id}.pdf",
            file_data,
            "application/pdf",
        )

        try:
            email.send()
            messages.success(request, "Email sent successfully")

        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")

        return JsonResponse({"status": "success"}, status=200)

    else:
        return JsonResponse(
            {"status": "failed", "error": "Not a POST request."}, status=400
        )


from django.views.generic.list import ListView


class PDFAngebotsListView(LoginRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/pdf_angebot_created.html"
    context_object_name = "angebots"

    def get_queryset(self):
        # Initial queryset filters
        queryset = (
            super()
            .get_queryset()
            .filter(user=self.request.user, angebot_id_assigned=True, status="bekommen")
        )
        query = self.request.GET.get("q")
        if query:
            queryset = filter_user_angebots_by_query(queryset, query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_angebots = context["angebots"]

        # Generating angebots and URLs
        angebots_and_urls = [
            (
                angebot,
                reverse("vertrieb_interface:serve_pdf", args=[angebot.angebot_id]),
                replace_spaces_with_underscores(angebot.name),
            )
            for angebot in user_angebots
            if angebot.angebot_pdf
        ]

        # Update context with the zipped angebots
        context.update(
            {
                "zipped_angebots": angebots_and_urls,
            }
        )
        return context


def get_angebots_and_urls(user_angebots):
    """Generate a list of tuples containing angebot, URL, and name with underscores."""
    return [
        (
            angebot,
            reverse("vertrieb_interface:serve_pdf", args=[angebot.angebot_id]),
            replace_spaces_with_underscores(angebot.name),
        )
        for angebot in user_angebots
        if angebot.angebot_pdf
    ]


def filter_user_angebots_by_query(user_angebots, query):
    """Filter user angebots based on the given query."""
    query_conditions = (
        Q(zoho_kundennumer__icontains=query)
        | Q(angebot_id__icontains=query)
        | Q(status__icontains=query)
        | Q(name__icontains=query)
        | Q(anfrage_vom__icontains=query)
    )
    return user_angebots.filter(query_conditions)


class PDFAngebotsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/pdf_angebot_created.html"
    context_object_name = "angebots"

    def test_func(self):
        return vertrieb_check(self.request.user)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(user=self.request.user, angebot_id_assigned=True, status="bekommen")
        )
        query = self.request.GET.get("q")
        if query:
            queryset = filter_user_angebots_by_query(queryset, query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_angebots = context["angebots"]
        context["zipped_angebots"] = get_angebots_and_urls(user_angebots)
        return context


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(vertrieb_check), name="dispatch")
class PDFAngebotsListView(PDFAngebotsListView):
    pass


@user_passes_test(vertrieb_check)
def PDFCalculationsListView(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = vertrieb_angebot.user
    if request.user != vertrieb_angebot.user and not request.user.is_staff:
        return page_not_found(request, Exception())
    user_angebots = VertriebAngebot.objects.filter(user=user)

    calc_path = os.path.join(settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Kalkulationen/")  # type: ignore
    name = replace_spaces_with_underscores(vertrieb_angebot.name)

    calc_files = [
        os.path.join(calc_path, f"Kalkulation_{name}_{vertrieb_angebot.angebot_id}.pdf")
        for angebot in user_angebots
    ]

    zipped_calculations = zip(user_angebots, calc_files)

    return render(
        request,
        "vertrieb/pdf_calculations_created.html",
        {
            "user": user,
            "zipped_calculations": zipped_calculations,
        },
    )


def fetch_ticket_status_pva_data(self, request, angebot_id):
    fetched_angebote_list = []
    vertrieb_angebot = VertriebAngebot.objects.get(status=angebot_id, user=request.user)
    zoho_id = vertrieb_angebot.zoho_id
    if zoho_id is not None:
        item = fetch_angenommen_status(request, zoho_id)
        fetched_data = {
            "zoho_id": item.get("ID", ""),
            "status": item.get("Status", ""),
            "status_pva": item.get("Status_PVA", ""),
            "angebot_bekommen_am": item.get("Angebot_bekommen_am", ""),
            "anrede": item.get("Name", {}).get("prefix", ""),
            "strasse": item.get("Adresse_PVA", {}).get("address_line_1", ""),
            "ort": item.get("Adresse_PVA", {}).get("postal_code", "")
            + " "
            + item.get("Adresse_PVA", {}).get("district_city", ""),
            "postanschrift_longitude": item.get("Adresse_PVA", {}).get("longitude", ""),
            "postanschrift_latitude": item.get("Adresse_PVA", {}).get("latitude", ""),
            "telefon_festnetz": item.get("Telefon_Festnetz", ""),
            "telefon_mobil": item.get("Telefon_mobil", ""),
            "zoho_kundennumer": item.get("Kundennummer", ""),
            "email": item.get("Email", ""),
            "notizen": item.get("Notizen", ""),
            "name": item.get("Name", {}).get("last_name", "")
            + " "
            + item.get("Name", {}).get("suffix", "")
            + " "
            + item.get("Name", {}).get("first_name", ""),
            "vertriebler_display_value": item.get("Vertriebler", {}).get(
                "display_value", ""
            ),
            "vertriebler_id": item.get("Vertriebler", {}).get("ID", ""),
            "adresse_pva_display_value": item.get("Adresse_PVA", {}).get(
                "display_value", ""
            ),
            "anfrage_vom": item.get("Anfrage_vom", ""),
        }
        vertrieb_angebot.ag_fetched_data = json.dumps(fetched_data)
        vertrieb_angebot.save()
    else:
        pass


@user_passes_test(vertrieb_check)
def PDFTicketListView(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = vertrieb_angebot.user
    if request.user != vertrieb_angebot.user and not request.user.is_staff:
        return page_not_found(request, Exception())
    user_angebots = VertriebAngebot.objects.filter(user=user)

    ticket_path = os.path.join(settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Tickets/")  # type: ignore

    ticket_files = [
        os.path.join(
            ticket_path,
            f"Ticket_{vertrieb_angebot.name}_{vertrieb_angebot.angebot_id}.pdf",
        )
        for angebot in user_angebots
    ]

    zipped_tickets = zip(user_angebots, ticket_files)

    return render(
        request,
        "vertrieb/pdf_ticket_created.html",
        {
            "user": user,
            "zipped_tickets": zipped_tickets,
        },
    )


class UpdateAdminAngebot(AdminRequiredMixin, VertriebCheckMixin, UpdateView):
    model = VertriebAngebot
    template_name = "vertrieb/view_orders_admin.html"
    fields = [
        "zoho_kundennumer",
        "angebot_id",
        "is_locked",
        "status",
        "name",
        "anfrage_vom",
        "name",
        "is_synced",
    ]

    def get_success_url(self):
        return reverse("vertrieb_interface:view_orders")


@method_decorator(csrf_exempt, name="dispatch")
class UpdateVertriebAngebotView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        vertriebAngebot = get_object_or_404(
            VertriebAngebot, angebot_id=self.kwargs.get("angebot_id")
        )
        vertriebAngebot.verbrauch = data.get("verbrauch")
        vertriebAngebot.grundpreis = data.get("grundpreis")
        vertriebAngebot.arbeitspreis = data.get("arbeitspreis")
        vertriebAngebot.prognose = data.get("prognose")
        vertriebAngebot.zeitraum = data.get("zeitraum")
        vertriebAngebot.bis10kWp = data.get("bis10kWp")
        vertriebAngebot.bis40kWp = data.get("bis40kWp")
        vertriebAngebot.ausrichtung = data.get("ausrichtung")
        vertriebAngebot.save()
        return JsonResponse({"status": "success"})


def get_data(request):
    data = VertriebAngebot.objects.all().values()
    return JsonResponse(list(data), safe=False)


def calc_graph_display(request):
    return render(request, "vertrieb/edit_angebot.html")
