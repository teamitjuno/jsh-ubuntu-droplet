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
from django.db.models import Count, IntegerField, Q, Sum, Case, When, Value, F
from django.db.models.functions import Cast
from django.http import (
    FileResponse,
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

# Local imports from 'config'
from config.settings import EMAIL_BACKEND, TELEGRAM_LOGGING

# Local imports from 'prices'
from prices.models import SolarModulePreise

# Local imports from 'calculator'
from calculator.models import Calculator
from calculator.forms import CalculatorForm

# Local imports from 'datenblatter'
from datenblatter.models import Datenblatter


# Local imports from 'vertrieb_interface'
from vertrieb_interface.forms import (
    VertriebAngebotForm,
    VertriebAngebotEmailForm,
    VertriebTicketForm,
)
from vertrieb_interface.api_views.zoho_operations_aktualisierung import (
    load_user_angebots,
)
from vertrieb_interface.zoho_api_connector import (
    fetch_angenommen_status,
    fetch_user_angebote_all,
)
from vertrieb_interface.models import CustomLogEntry, VertriebAngebot, VertriebTicket
from vertrieb_interface.pdf_services import (
    angebot_pdf_creator_user,
    ticket_pdf_creator_user,
    calc_pdf_creator,
    ticket_pdf_creator,
)
from vertrieb_interface.permissions import admin_required, AdminRequiredMixin
from vertrieb_interface.telegram_logs_sender import (
    send_message_to_bot,
    send_custom_message,
)

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


def handler404(request, exception):
    return render(request, "404.html", status=404)


def vertrieb_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class VertriebCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return vertrieb_check(self.request.user)


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

    angenommen_criteria = (
        Q(status="angenommen")
        & ~Q(status_pva="")
        & Q(angebot_id=F("angenommenes_angebot"))
    )

    angenommen_count = vertriebangebots.filter(angenommen_criteria).count()
    all_count = vertriebangebots.count()
    bekommen_count = vertriebangebots.filter(status="bekommen", is_locked=True).count()
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
                default=Value(0),  # or another appropriate default value
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

    form_angebot = VertriebAngebotForm(request.POST or initial_data, user=user)
    if form_angebot.is_valid():
        vertrieb_angebot = form_angebot.save(commit=False)
        vertrieb_angebot.created_at = timezone.now()
        vertrieb_angebot.current_date = datetime.datetime.now()

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

        return page_not_found(request, Exception())

    return render(request, "vertrieb/edit_angebot.html", {"form_angebot": form_angebot})


@user_passes_test(vertrieb_check)
def create_ticket_new(request):
    user = request.user

    initial_data = {
        "anz_speicher": user.initial_anz_speicher,
        "wandhalterung_fuer_speicher": user.initial_wandhalterung_fuer_speicher,
        "solar_module": user.initial_solar_module,
        "modulanzahl": user.initial_modulanzahl,
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

    form_ticket = VertriebTicketForm(request.POST or initial_data, user=user)

    if TELEGRAM_LOGGING:
        send_custom_message(user, "erstellt ein neues Angebot", "📄")

    if form_ticket.is_valid():
        vertrieb_ticket = form_ticket.save(commit=False)
        vertrieb_ticket.user = user
        vertrieb_ticket.save()
        return redirect("vertrieb_interface:edit_ticket_new", vertrieb_ticket.ticket_id)

    if request.POST and "create_blank_ticket_new" in request.POST:
        blank_ticket = VertriebTicket(user=user)
        blank_ticket.created_at = timezone.now()
        blank_ticket.current_date = datetime.datetime.now()
        blank_ticket.anz_speicher = user.initial_anz_speicher
        blank_ticket.wandhalterung_fuer_speicher = (
            user.initial_wandhalterung_fuer_speicher
        )
        blank_ticket.solar_module = user.initial_solar_module
        blank_ticket.modulanzahl = user.initial_modulanzahl
        blank_ticket.text_for_email = user.initial_text_for_email
        blank_ticket.save()
        return HttpResponseRedirect(
            reverse("vertrieb_interface:edit_ticket_new", args=[blank_ticket.ticket_id])
        )

    if not form_ticket.is_valid():

        return page_not_found(request, Exception())

    return render(request, "vertrieb/edit_ticket_new.html", {"form_ticket": form_ticket})



def map_view(request, angebot_id, *args, **kwargs):
    vertrieb_angebot = VertriebAngebot.objects.get(
        angebot_id=angebot_id, user=request.user
    )

    context = {
        "LATITUDE": vertrieb_angebot.postanschrift_latitude,
        "LONGITUDE": vertrieb_angebot.postanschrift_longitude,
    }
    return render(request, "vertrieb/extra/map.html", context)


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
            send_custom_message(self.request.user, "Hat ein Angebot gelöscht", "Info")
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


class DeleteUserTicket(DeleteView):
    model = VertriebTicket
    template_name = "vertrieb/view_orders_ticket.html"

    def get_success_url(self):
        return reverse("vertrieb_interface:view_orders_ticket")

    def get_object(self, queryset=None):
        return VertriebTicket.objects.get(ticket_id=self.kwargs["ticket_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if TELEGRAM_LOGGING:
            send_custom_message(self.request.user, "Hat ein Ticket gelöscht", "Info")
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


def delete_unexisting_records(request):
    user = request.user

    try:
        user_data = json.loads(user.zoho_data_text) if user.zoho_data_text else []
        if not user_data:
            return HttpResponse("No data found in user's Zoho data.", status=200)

        user_zoho_ids = {item.get("zoho_id") for item in user_data}

        # Query only once to get angebots that might need updating
        vertrieb_angebots = VertriebAngebot.objects.filter(
            user=user, angebot_id_assigned=True
        )

        # Filter those that don't match the Zoho IDs to update
        vertrieb_angebots_to_update = vertrieb_angebots.exclude(
            zoho_id__in=user_zoho_ids
        )
        vertrieb_angebots_to_update.update(angebot_id_assigned=False)

        return HttpResponse(
            f"Updated {vertrieb_angebots_to_update.count()} records.", status=200
        )

    except json.JSONDecodeError:
        return HttpResponse("Failed to decode JSON from user's Zoho data.", status=400)
    except Exception as e:
        return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)


def update_status_to_angenommen(request):

    user = request.user
    user_data = json.loads(user.zoho_data_text)
    user_zoho_ids = {item["zoho_id"] for item in user_data}

    zoho_id_to_status = {item["zoho_id"]: item["status"] for item in user_data}
    zoho_id_to_status_PVA = {item["zoho_id"]: item["status_pva"] for item in user_data}
    zoho_id_to_angenommenes_angebot = {
        item["zoho_id"]: item["angenommenes_angebot"] for item in user_data
    }

    vertrieb_angebots_to_update = VertriebAngebot.objects.filter(
        user=user,
        angebot_id_assigned=True,
    ).filter(zoho_id__in=user_zoho_ids)

    for angebot in vertrieb_angebots_to_update:
        angebot.status = zoho_id_to_status.get(angebot.zoho_id)
        angebot.status_pva = zoho_id_to_status_PVA.get(angebot.zoho_id)
        angebot.angenommenes_angebot = zoho_id_to_angenommenes_angebot.get(
            angebot.zoho_id
        )
        angebot.save()
        if angebot.angenommenes_angebot == angebot.angebot_id:
            angebot.angebot_id_assigned = True

            angebot.save()
        elif (
            angebot.angenommenes_angebot != angebot.angebot_id
            and angebot.status == "angenommen"
        ):
            angebot.angebot_id_assigned = False
            angebot.save()
        else:
            pass


def replace_spaces_with_underscores(s: str) -> str:
    return s.replace(" ", "_").replace(",","")


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

    pdf_content = angebot_pdf_creator_user.createOfferPdf(
        data,
        vertrieb_angebot,
        certifikate,
        user,
        True,
    )
    vertrieb_angebot.angebot_pdf = pdf_content
    vertrieb_angebot.save()

    return redirect("vertrieb_interface:document_view", angebot_id=angebot_id)


@login_required
def create_calc_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data
    name = replace_spaces_with_underscores(vertrieb_angebot.name)

    pdf_content = calc_pdf_creator.createCalcPdf(
        data,
        vertrieb_angebot,
        user,
    )
    vertrieb_angebot.calc_pdf = pdf_content
    vertrieb_angebot.save()

    return redirect("vertrieb_interface:document_calc_view", angebot_id=angebot_id)


@login_required
def create_ticket_new_pdf_user(request, ticket_id):
    vertrieb_ticket = get_object_or_404(VertriebTicket, ticket_id=ticket_id)
    user = request.user
    data = vertrieb_ticket.data
    certifikate = user.user_certifikate

    pdf_content = ticket_pdf_creator_user.createOfferPdf(
        data,
        vertrieb_ticket,
        certifikate,
        user,
    )
    vertrieb_ticket.ticket_pdf = pdf_content
    vertrieb_ticket.save()

    return redirect("vertrieb_interface:document_view", ticket_id=ticket_id)


@login_required
def create_ticket_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data

    pdf_content = ticket_pdf_creator.createTicketPdf(data)
    vertrieb_angebot.ticket_pdf = pdf_content
    vertrieb_angebot.save()
    return redirect("vertrieb_interface:document_ticket_view", angebot_id=angebot_id)


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
def serve_calc_pdf(request, angebot_id):
    decoded_angebot_id = unquote(angebot_id)
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=decoded_angebot_id)
    name = replace_spaces_with_underscores(vertrieb_angebot.name)
    filename = f"Kalkulation_{name}_{vertrieb_angebot.angebot_id}.pdf"
    sleep(0.5)
    if not vertrieb_angebot.calc_pdf:
        return StreamingHttpResponse("File not found.", status=404)

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

    async_iterator = AsyncFileIter(vertrieb_angebot.ticket_pdf)

    response = StreamingHttpResponse(async_iterator, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response

@login_required
def serve_ticket_new_pdf(request, ticket_id):
    decoded_ticket_id = unquote(ticket_id)
    vertrieb_ticket = get_object_or_404(VertriebTicket, ticket_id=decoded_ticket_id)
    name = replace_spaces_with_underscores(vertrieb_ticket.name)
    filename = f"{name}_{vertrieb_ticket.ticket_id}.pdf"
    sleep(0.5)

    if not vertrieb_ticket.ticket_pdf:
        return StreamingHttpResponse("File not found.", status=404)

    async_iterator = AsyncFileIter(vertrieb_ticket.ticket_pdf)

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
        subject = f"Angebot Photovoltaikanlage {angebot_id}"
        body = text_for_email
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


def get_angebots_and_urls(user_angebots):
    """
    Generate a list of tuples containing angebot, URL, and name with underscores.
    """
    result = []
    for angebot in user_angebots:
        if angebot.angebot_pdf:
            url = reverse("vertrieb_interface:serve_pdf", args=[angebot.angebot_id])
        else:
            continue
        name_with_underscores = replace_spaces_with_underscores(angebot.name)
        result.append((angebot, url, name_with_underscores))
    return result


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

    calc_path = os.path.join(
        settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Kalkulationen/"
    )
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
            "angenommenes_angebot": item.get("Angenommenes_Angebot", ""),
        }
        vertrieb_angebot.ag_fetched_data = json.dumps(fetched_data)
        vertrieb_angebot.save()
    else:
        pass


# def PDFTicketListView(request, angebot_id):
#     vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
#     user = vertrieb_angebot.user
#     if request.user != vertrieb_angebot.user and not request.user.is_staff:
#         return page_not_found(request, Exception())
#     user_angebots = VertriebAngebot.objects.filter(user=user, status="angenommen", angennommenes_angebot == angebot_id)

#     ticket_path = os.path.join(
#         settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Tickets/"
#     )

#     ticket_files = [
#         os.path.join(
#             ticket_path,
#             f"Ticket_{vertrieb_angebot.name}_{vertrieb_angebot.angebot_id}.pdf",
#         )
#         for angebot in user_angebots
#     ]

#     zipped_tickets = zip(user_angebots, ticket_files)

#     return render(
#         request,
#         "vertrieb/pdf_ticket_created.html",
#         {
#             "user": user,
#             "zipped_tickets": zipped_tickets,
#         },
#     )


@user_passes_test(vertrieb_check)
def pdfticket_list_view(request, angebot_id):
    # Fetch the specific VertriebAngebot instance or return 404
    vertrieb_angebot = get_object_or_404(VertriebAngebot, id=angebot_id)

    # Check user permission
    if request.user != vertrieb_angebot.user and not request.user.is_staff:
        raise PermissionDenied

    # Filter accepted offers based on the criteria
    accepted_offers = VertriebAngebot.objects.filter(
        user=vertrieb_angebot.user,
        id=vertrieb_angebot.angenommenes_angebot,
        status="angenommen",
    )

    # Prepare the URLs for the PDF tickets of accepted offers
    ticket_url_base = f"{settings.MEDIA_URL}pdf/usersangebots/{vertrieb_angebot.user.username}/Tickets/"
    ticket_files = [
        f"{ticket_url_base}Ticket_{offer.name}_{offer.id}.pdf"
        for offer in accepted_offers
    ]

    # Pair each offer with its corresponding ticket file URL
    zipped_tickets = zip(accepted_offers, ticket_files)

    # Render the PDF ticket list page
    return render(
        request,
        "vertrieb/pdf_ticket_created.html",
        {"user": vertrieb_angebot.user, "zipped_tickets": zipped_tickets},
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
