# Python standard libraries
import os
import io
import json
import datetime
from pprint import pformat, pp
from urllib.parse import unquote

# Django related imports
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, Http404, JsonResponse, FileResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.formats import date_format
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models.functions import Cast
from django.db.models import IntegerField, Q, Sum, Count
from django.views.defaults import page_not_found
from django.conf import settings

# Third party libraries
from dotenv import load_dotenv

# Local imports
from config import settings
from config.settings import ENV_FILE, EMAIL_BACKEND
from prices.models import SolarModulePreise
from calculator.models import Calculator
from calculator.forms import CalculatorForm
from shared.chat_bot import handle_message
from vertrieb_interface.get_user_angebots import (
    fetch_user_angebote_all,
    fetch_current_user_angebot,
    fetch_angenommen_status,
    pushAngebot,
)
from vertrieb_interface.models import VertriebAngebot, CustomLogEntry
from vertrieb_interface.forms import VertriebAngebotForm
from vertrieb_interface.utils import load_vertrieb_angebot
from vertrieb_interface.pdf_services import (
    angebot_pdf_creator,
    angebot_pdf_creator_user,
    calc_pdf_creator,
    ticket_pdf_creator,
)
from vertrieb_interface.permissions import admin_required, AdminRequiredMixin
from .models import VertriebAngebot
from authentication.models import User
from authentication.forms import TopVerkauferContainerViewForm


now = timezone.now()
now_localized = timezone.localtime(now)
now_german = date_format(now_localized, "DATETIME_FORMAT")

load_dotenv(ENV_FILE)


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
            activity = {
                "action_time": entry.action_time,
                "module": entry.content_type.model_class()._meta.verbose_name_plural,
                "action": {
                    "message": entry.get_change_message(),
                    "class": "text-danger"
                    if entry.get_vertrieb_angebot().status == "abgelaufen"
                    else "text-warning"
                    if entry.get_vertrieb_angebot().status == "bekommen"
                    else "text-success"
                    if entry.get_vertrieb_angebot().status == "angenommen"
                    else "text-primary"
                    if entry.action_flag == ADDITION
                    else "text-info"
                    if entry.action_flag == CHANGE
                    else "text-danger",
                },
                "user": entry.user,
                "object": {
                    "repr": entry.object_repr,
                    "class": "text-danger"
                    if entry.get_vertrieb_angebot().status == "abgelaufen"
                    else "text-warning"
                    if entry.get_vertrieb_angebot().status == "bekommen"
                    else "text-success"
                    if entry.get_vertrieb_angebot().status == "angenommen"
                    else "text-primary"
                    if entry.action_flag == ADDITION
                    else "text-info"
                    if entry.action_flag == CHANGE
                    else "text-danger",
                },
                "icon": "mdi-delete bg-danger-lighten text-danger"
                if entry.get_vertrieb_angebot().status == "abgelaufen"
                else "mdi-minus bg-warning-lighten text-warning"
                if entry.get_vertrieb_angebot().status == "bekommen"
                else "mdi-update bg-success-lighten text-success"
                if entry.get_vertrieb_angebot().status == "angenommen"
                else "mdi-plus bg-primary-lighten text-primary"
                if entry.action_flag == ADDITION
                else "mdi-update bg-info-lighten text-info"
                if entry.action_flag == CHANGE
                else "mdi-delete bg-danger-lighten text-danger",
                "status": status,
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
        queryset = self.model.objects.filter(  # type: ignore
            user=self.request.user, status="angenommen", angebot_id_assigned=True
        )

        queryset = queryset.annotate(
            zoho_kundennumer_int=Cast("zoho_kundennumer", IntegerField())
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
        form = TopVerkauferContainerViewForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Setting updated successfully!")
            return redirect("vertrieb_interface:profile")
    else:
        form = TopVerkauferContainerViewForm(instance=request.user)
    context = {"user": user, "form": form}
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
        response = handle_message(question)
        return JsonResponse({"response": response})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)


@user_passes_test(vertrieb_check)
def create_angebot(request):
    form_angebot = VertriebAngebotForm(request.POST or None, user=request.user)
    print(request.user, "Neue Angebot created")
    if form_angebot.is_valid():
        vertrieb_angebot = form_angebot.save(commit=False, user=request.user)
        vertrieb_angebot.user = request.user

        vertrieb_angebot.save()

        return redirect("vertrieb_interface:edit_angebot", vertrieb_angebot.angebot_id)

    if request.POST and "create_blank_angebot" in request.POST:
        blank_angebot = VertriebAngebot(user=request.user)
        blank_angebot.created_at = timezone.now()
        blank_angebot.current_date = datetime.datetime.now()

        blank_angebot.save()
        # CustomLogEntry.objects.log_action(
        #         user_id=request.user.id,
        #         content_type_id=ContentType.objects.get_for_model(blank_angebot).pk,
        #         object_id=blank_angebot.angebot_id,
        #         object_repr=str(blank_angebot),
        #         action_flag=ADDITION
        #     )
        return HttpResponseRedirect(
            reverse("vertrieb_interface:edit_angebot", args=[blank_angebot.angebot_id])
        )

    if not form_angebot.is_valid():
        print(form_angebot.errors)
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
            self.data = fetch_user_angebote_all(request)
            zoho_data = json.dumps(self.data)

            profile.zoho_data_text = zoho_data  # type: ignore
            profile.save()
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

    def dispatch(self, request, *args, **kwargs):
        angebot_id = kwargs.get("angebot_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        self.handle_status_change(angebot_id)
        self.handle_zoho_status_change(request, angebot_id)
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
                    print("Angebot saved with status 'abgelaufen'")
                    CustomLogEntry.objects.log_action(
                        user_id=angebot.user_id,
                        content_type_id=ContentType.objects.get_for_model(angebot).pk,
                        object_id=angebot.pk,
                        object_repr=str(angebot),
                        action_flag=CHANGE,
                        status=angebot.status,
                    )

    def handle_zoho_status_change(self, request, angebot_id):
        user=request.user
        

        try:
            vertrieb_angebot = VertriebAngebot.objects.get(
                angebot_id=angebot_id, user=request.user
            )
            
            if vertrieb_angebot.angebot_id_assigned == True and vertrieb_angebot.zoho_id:
                zoho_id = vertrieb_angebot.zoho_id
                print(f"{user.email}: Handling status change... ANGEBOT_ZOHO_ID : ", (vertrieb_angebot.zoho_id), (vertrieb_angebot.vorname_nachname))
                fetched_angebote = fetch_angenommen_status(request, zoho_id)
                print("Angebot status handled: ", fetched_angebote.get("Status"))
                if fetched_angebote and fetched_angebote.get("Status") == "angenommen":
                    vertrieb_angebot.status = "angenommen"
                    vertrieb_angebot.status_change_field = None
                    vertrieb_angebot.save()
                    print("Angebot saved with status 'angenommen'")
                    # Assuming you want to create a form instance with the fetched data
                    form = self.form_class(
                        fetched_angebote, instance=vertrieb_angebot, user=request.user
                    )

                    if form.is_valid():
                        form.save()
                # elif fetched_angebote and fetched_angebote.get("Status") != "bekommen":
                #     status = fetched_angebote.get("Status")

                #     vertrieb_angebot.status = status

                #     vertrieb_angebot.save()
                #     # Assuming you want to create a form instance with the fetched data
                #     form = self.form_class(
                #         fetched_angebote, instance=vertrieb_angebot, user=request.user
                #     )

                #     if form.is_valid():
                #         form.save()
            else:
                pass
        except VertriebAngebot.DoesNotExist:
            pass

    def get(self, request, angebot_id, *args, **kwargs):
        vertrieb_angebot = VertriebAngebot.objects.get(
            angebot_id=angebot_id, user=request.user
        )
        zoho_id = vertrieb_angebot.zoho_id
        if zoho_id is not None:
            data = fetch_current_user_angebot(request, zoho_id)

            for item in data:
                vertrieb_angebot.vorname_nachname = vertrieb_angebot.name
                vertrieb_angebot.anfrage_ber = item["anfrage_berr"]

                vertrieb_angebot.angebot_bekommen_am = (
                    item["angebot_bekommen_am"] if item["angebot_bekommen_am"] else ""
                )

                vertrieb_angebot.verbrauch = item["verbrauch"]

                vertrieb_angebot.leadstatus = (
                    item["leadstatus"] if item["leadstatus"] else ""
                )
                vertrieb_angebot.notizen = item["notizen"]
                vertrieb_angebot.email = item["email"]
                vertrieb_angebot.postanschrift_latitude = item["latitude"]
                vertrieb_angebot.postanschrift_longitude = item["longitude"]

                vertrieb_angebot.empfohlen_von = item["empfohlen_von"]
                vertrieb_angebot.termine_text = item["termine_text"]
                vertrieb_angebot.termine_id = item["termine_id"]
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
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)  # type: ignore

        if "change_status_button" in request.POST:
            if form.is_valid():
                form.instance.status = "angenommen"  # type:ignore
                form.save()  # type:ignore
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
                    "vertrieb_interface:edit_angebot", vertrieb_angebot.angebot_id
                )
        if "angebotsumme_rechnen" in request.POST:
            print(f"{user.email}: Angebotsumme rechnen für ANGEBOT_ZOHO_ID : ", (vertrieb_angebot.zoho_id), (vertrieb_angebot.vorname_nachname))
            if form.is_valid():
                data = json.loads(user.zoho_data_text or '[["test", "test"]]')
                name_to_kundennumer = {
                    item["name"]: item["zoho_kundennumer"] for item in data
                }
                name_to_zoho_id = {
                    item["name"]: item["zoho_id"] for item in data
                }
                name = form.cleaned_data["name"]
                zoho_id = form.cleaned_data["zoho_id"]
                kundennumer = name_to_kundennumer[name]
                zoho_id = name_to_zoho_id[name]
                vertrieb_angebot.zoho_kundennumer = kundennumer
                vertrieb_angebot.zoho_id = int(zoho_id)
                if vertrieb_angebot.angebot_id_assigned == True:
                    vertrieb_angebot.angebot_id_assigned = True
                    vertrieb_angebot.save()
                    print("Angebot", (vertrieb_angebot.zoho_id), "assigned with ID ", (vertrieb_angebot.angebot_id))
                    form.save()  # type:ignore
                else:
                    vertrieb_angebot.angebot_id_assigned = False
                    vertrieb_angebot.save()
                    print("Angebot", (vertrieb_angebot.zoho_id), "saved with no assign")
                    form.save()  # type:ignore
                return redirect(
                    "vertrieb_interface:edit_angebot", vertrieb_angebot.angebot_id
                )
        if "bekommen_zu_machen" in request.POST:
            print(f"{user.email}: Creating PDF für ANGEBOT_ZOHO_ID : ", (vertrieb_angebot.zoho_id), (vertrieb_angebot.vorname_nachname))
            if form.is_valid():
                data = json.loads(user.zoho_data_text or '[["test", "test"]]')
                name_to_kundennumer = {
                    item["name"]: item["zoho_kundennumer"] for item in data
                }
                name_to_zoho_id = {
                    item["name"]: item["zoho_id"] for item in data
                }
                name = form.cleaned_data["name"]
                zoho_id = form.cleaned_data["zoho_id"]
                kundennumer = name_to_kundennumer[name]
                print("Kundennummer:", kundennumer)
                zoho_id = name_to_zoho_id[name]
                
                vertrieb_angebot.zoho_kundennumer = kundennumer
                vertrieb_angebot.zoho_id = int(zoho_id)
                vertrieb_angebot.save()
                form.instance.status = "bekommen"
                vertrieb_angebot.angebot_id_assigned = True
                print("Changing status to ", vertrieb_angebot.status)
                pushAngebot(vertrieb_angebot, user_zoho_id)
                print("Pushing data to Zoho was successfull!")
                form.save()  # type:ignore

                return redirect(
                    "vertrieb_interface:create_angebot_pdf_user", vertrieb_angebot.angebot_id
                )

        elif form.is_valid():
            print(f"{user.email}: Saving Angebot für ANGEBOT_ZOHO_ID : ", (vertrieb_angebot.zoho_id), (vertrieb_angebot.vorname_nachname))
            vertrieb_angebot.angebot_id_assigned = True

            data = json.loads(user.zoho_data_text or '[["test", "test"]]')
            name_to_kundennumer = {
                item["name"]: item["zoho_kundennumer"] for item in data
            }
            name_to_zoho_id = {
                item["name"]: item["zoho_id"] for item in data
            }
            name = form.cleaned_data["name"]
            zoho_id = form.cleaned_data["zoho_id"]
            kundennumer = name_to_kundennumer[name]
            
            zoho_id = name_to_zoho_id[name]
            
            vertrieb_angebot.zoho_kundennumer = kundennumer
            vertrieb_angebot.zoho_id = int(zoho_id)
            vertrieb_angebot.save()
            form.save()  # type:ignore
            print(f"{user.email}: Saving successfull!", vertrieb_angebot.angebot_id)
            CustomLogEntry.objects.log_action(
                user_id=vertrieb_angebot.user_id,
                content_type_id=ContentType.objects.get_for_model(vertrieb_angebot).pk,
                object_id=vertrieb_angebot.pk,
                object_repr=str(vertrieb_angebot),
                action_flag=CHANGE,
                status=vertrieb_angebot.status,
            )
            return redirect(
                "vertrieb_interface:edit_angebot", vertrieb_angebot.angebot_id
            )
        print(f"{user.email}: Saving unsuccessfull! Form not valid", vertrieb_angebot.angebot_id)
        return self.form_invalid(form, vertrieb_angebot)

    def form_invalid(self, form, vertrieb_angebot, *args, **kwargs):
        context = self.get_context_data()
        countdown = vertrieb_angebot.countdown()
        context["status_change_field"] = vertrieb_angebot.status_change_field
        context["countdown"] = vertrieb_angebot.countdown()
        context["vertrieb_angebot"] = vertrieb_angebot
        context["form"] = form
        return render(self.request, self.template_name, context)

    def load_data_from_zoho_to_angebot_id(self, request):
        pass


class TicketEditView(LoginRequiredMixin, VertriebCheckMixin, FormMixin, View):
    model = VertriebAngebot
    form_class = VertriebAngebotForm
    template_name = "vertrieb/edit_ticket.html"
    context_object_name = "vertrieb_angebot"

    def dispatch(self, request, *args, **kwargs):
        angebot_id = kwargs.get("angebot_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        self.handle_status_change(angebot_id)
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

    def get(self, request, angebot_id, *args, **kwargs):
        vertrieb_angebot = VertriebAngebot.objects.get(
            angebot_id=angebot_id, user=request.user
        )
        zoho_id = vertrieb_angebot.zoho_id

        data = fetch_current_user_angebot(request, zoho_id)

        for item in data:
            vertrieb_angebot.vorname_nachname = vertrieb_angebot.name
            vertrieb_angebot.anfrage_ber = item["anfrage_berr"]

            vertrieb_angebot.angebot_bekommen_am = (
                item["angebot_bekommen_am"] if item["angebot_bekommen_am"] else ""
            )

            vertrieb_angebot.verbrauch = item["verbrauch"]

            vertrieb_angebot.leadstatus = (
                item["leadstatus"] if item["leadstatus"] else ""
            )
            vertrieb_angebot.notizen = item["notizen"]
            vertrieb_angebot.email = item["email"]
            vertrieb_angebot.postanschrift_latitude = item["latitude"]
            vertrieb_angebot.postanschrift_longitude = item["longitude"]

            vertrieb_angebot.empfohlen_von = item["empfohlen_von"]
            vertrieb_angebot.termine_text = item["termine_text"]
            vertrieb_angebot.termine_id = item["termine_id"]
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

    def post(self, request, *args, **kwargs):
        vertrieb_angebot = get_object_or_404(
            VertriebAngebot, angebot_id=self.kwargs.get("angebot_id")
        )
        user = request.user
        form = self.form_class(request.POST, instance=vertrieb_angebot, user=user)  # type: ignore

        if "change_status_button" in request.POST:
            if form.is_valid():
                form.instance.status = "angenommen"  # type:ignore
                form.save()  # type:ignore
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
                    "vertrieb_interface:edit_ticket", vertrieb_angebot.angebot_id
                )

        elif form.is_valid():
            vertrieb_angebot.angebot_id_assigned = True

            data = json.loads(user.zoho_data_text or '[["test", "test"]]')
            name_to_kundennumer = {
                item["name"]: item["zoho_kundennumer"] for item in data
            }
            name = form.cleaned_data["name"]
            kundennumer = name_to_kundennumer[name]
            vertrieb_angebot.zoho_kundennumer = kundennumer

            form.save()  # type:ignore
            CustomLogEntry.objects.log_action(
                user_id=vertrieb_angebot.user_id,
                content_type_id=ContentType.objects.get_for_model(vertrieb_angebot).pk,
                object_id=vertrieb_angebot.pk,
                object_repr=str(vertrieb_angebot),
                action_flag=CHANGE,
                status=vertrieb_angebot.status,
            )
            return redirect(
                "vertrieb_interface:edit_ticket", vertrieb_angebot.angebot_id
            )

        return self.form_invalid(form, vertrieb_angebot)

    def form_invalid(self, form, vertrieb_angebot, *args, **kwargs):
        context = self.get_context_data()
        countdown = vertrieb_angebot.countdown()
        context["status_change_field"] = vertrieb_angebot.status_change_field
        context["countdown"] = vertrieb_angebot.countdown()

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


class ViewOrders(LoginRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/view_orders.html"
    context_object_name = "angebots"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.model.objects.filter(  # type: ignore
            user=self.request.user,
            angebot_id_assigned=True,
            zoho_kundennumer__regex=r"^\d+$",
        )

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(zoho_kundennumer__icontains=query)
                | Q(angebot_id__icontains=query)
                | Q(status__icontains=query)
                | Q(name__icontains=query)
                | Q(anfrage_vom__icontains=query)
            )

        queryset = queryset.annotate(
            zoho_kundennumer_int=Cast("zoho_kundennumer", IntegerField())
        )
        queryset = queryset.order_by("-zoho_kundennumer_int")

        return queryset


@user_passes_test(vertrieb_check)
def load_user_angebots(request):
    try:
        profile, created = User.objects.get_or_create(zoho_id=request.user.zoho_id)
        user = get_object_or_404(User, zoho_id=request.user.zoho_id)
        kurz = user.kuerzel  # type: ignore

        all_user_angebots_list = fetch_user_angebote_all(request)

        zoho_data = json.dumps(all_user_angebots_list)
        profile.zoho_data_text = zoho_data  # type: ignore
        profile.save()
        load_vertrieb_angebot(all_user_angebots_list, user, kurz)
        return JsonResponse({"status": "success"}, status=200)
    except Exception:
        return JsonResponse(
            {"status": "failed", "error": "Not a POST request."}, status=400
        )


def create_ticket_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    data = vertrieb_angebot.data

    pdf_content = ticket_pdf_creator.createTicketPdf(
        data,
    )
    vertrieb_angebot.ticket_pdf = pdf_content
    vertrieb_angebot.save()

    return redirect("vertrieb_interface:document_ticket_view", angebot_id=angebot_id)


@admin_required
def create_angebot_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = vertrieb_angebot.user
    data = vertrieb_angebot.data

    if vertrieb_angebot.angebot_pdf_admin is None:
        pdf_content = angebot_pdf_creator.createOfferPdf(
            data,
            vertrieb_angebot,
            user,
        )
        vertrieb_angebot.angebot_pdf_admin = pdf_content
        vertrieb_angebot.save()

    response = FileResponse(
        io.BytesIO(vertrieb_angebot.angebot_pdf_admin), content_type="application/pdf"
    )
    response[
        "Content-Disposition"
    ] = f"inline; filename=Angebot_{vertrieb_angebot.angebot_id}.pdf"
    return response


@login_required
def create_angebot_pdf_user(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data

    pdf_content = angebot_pdf_creator_user.createOfferPdf(
        data,
        vertrieb_angebot,
        user,
    )
    vertrieb_angebot.angebot_pdf = pdf_content
    vertrieb_angebot.save()

    return redirect("vertrieb_interface:document_view", angebot_id=angebot_id)


@login_required
def create_calc_pdf(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = request.user
    data = vertrieb_angebot.data

    pdf_content = calc_pdf_creator.createCalcPdf2(
        data,
        vertrieb_angebot,
        user,
    )
    vertrieb_angebot.calc_pdf = pdf_content
    vertrieb_angebot.save()

    pdf_link = os.path.join(settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Kalkulationen/Kalkulation_{vertrieb_angebot.angebot_id}.pdf")  # type: ignore

    return redirect("vertrieb_interface:document_calc_view", angebot_id=angebot_id)


@login_required
def document_view(request, angebot_id):
    pdf_url = reverse("vertrieb_interface:serve_pdf", args=[angebot_id])
    context = {"pdf_url": pdf_url, "angebot_id": angebot_id}
    return render(request, "vertrieb/document_view.html", context)


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
    filename = f"Angebot_{vertrieb_angebot.angebot_id}.pdf"

    response = FileResponse(
        vertrieb_angebot.angebot_pdf, content_type="application/pdf"
    )
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


@login_required
def serve_calc_pdf(request, angebot_id):
    decoded_angebot_id = unquote(angebot_id)
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=decoded_angebot_id)
    filename = f"Kalkulation_{vertrieb_angebot.angebot_id}.pdf"

    response = FileResponse(vertrieb_angebot.calc_pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


@login_required
def serve_ticket_pdf(request, angebot_id):
    decoded_angebot_id = unquote(angebot_id)
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=decoded_angebot_id)
    filename = f"Ticket_{vertrieb_angebot.angebot_id}.pdf"

    response = FileResponse(vertrieb_angebot.ticket_pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


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
            user.smtp_subject,
            user.smtp_body,
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

        vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
        pdf = vertrieb_angebot.angebot_pdf
        subject = f"Angebot Photovoltaikanlage {angebot_id}"
        geerter = f"Sehr geehrter {vertrieb_angebot.vorname_nachname}\n\n"
        body = geerter + user.smtp_body

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
        file_data = vertrieb_angebot.angebot_pdf.tobytes()  # type:ignore
        email.attach(
            f"Angebot_{vertrieb_angebot.angebot_id}.pdf", file_data, "application/pdf"
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
def send_calc_invoice(request, angebot_id):
    if request.method == "POST":
        user = request.user

        vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
        pdf = vertrieb_angebot.calc_pdf

        subject = f"Kalkulation Photovoltaikanlage {angebot_id}"
        geerter = f"Sehr geehrter {vertrieb_angebot.vorname_nachname}\n\n"
        body = geerter + user.smtp_body

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
            f"Kalkulation_{vertrieb_angebot.angebot_id}.pdf",
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
            f"Ticket_{vertrieb_angebot.angebot_id}.pdf",
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
@user_passes_test(vertrieb_check)
def pdf_angebots_list_view(request):
    user_angebots = VertriebAngebot.objects.filter(user=request.user)

    query = request.GET.get("q")
    if query:
        user_angebots = user_angebots.filter(
            Q(zoho_kundennumer__icontains=query)
            | Q(angebot_id__icontains=query)
            | Q(status__icontains=query)
            | Q(name__icontains=query)
            | Q(anfrage_vom__icontains=query)
        )

    angebots_and_urls = []

    for angebot in user_angebots:
        if angebot.angebot_pdf is not None:
            angebot_url = reverse(
                "vertrieb_interface:serve_pdf", args=[angebot.angebot_id]
            )
            angebots_and_urls.append((angebot, angebot_url))

    context = {
        "zipped_angebots": angebots_and_urls,
        "angebots": user_angebots,
    }

    return render(request, "vertrieb/pdf_angebot_created.html", context)


class PDFAngebotsListView(LoginRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/pdf_angebot_created.html"
    context_object_name = "angebots"

    def dispatch(self, request, *args, **kwargs):
        angebot_id = self.kwargs.get("angebot_id")
        vertrieb_angebot = get_object_or_404(self.model, angebot_id=angebot_id)  # type: ignore
        user = vertrieb_angebot.user  # type: ignore
        if not request.user.is_authenticated and self.request.user != user:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        angebot_id = self.kwargs.get("angebot_id")
        vertrieb_angebot = get_object_or_404(self.model, angebot_id=angebot_id)  # type: ignore
        user = vertrieb_angebot.user  # type: ignore

        if self.request.user != user and not self.request.user.is_staff:  # type: ignore
            raise Http404()

        user_angebots = self.model.objects.filter(user=user, angebot_id_assigned=True)  # type: ignore

        angebot_urls = [
            reverse("serve_pdf", args=[vertrieb_angebot.angebot_id])  # type:ignore
            for vertrieb_angebot in user_angebots
        ]

        self.extra_context = {
            "user": user,
            "zipped_angebots": zip(user_angebots, angebot_urls),
        }

        return user_angebots


@user_passes_test(vertrieb_check)
def PDFCalculationsListView(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = vertrieb_angebot.user
    if request.user != vertrieb_angebot.user and not request.user.is_staff:
        return page_not_found(request, Exception())
    user_angebots = VertriebAngebot.objects.filter(user=user)

    calc_path = os.path.join(settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Kalkulationen/")  # type: ignore

    calc_files = [
        os.path.join(calc_path, f"Kalkulation_{vertrieb_angebot.angebot_id}.pdf")
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


@user_passes_test(vertrieb_check)
def PDFTicketListView(request, angebot_id):
    vertrieb_angebot = get_object_or_404(VertriebAngebot, angebot_id=angebot_id)
    user = vertrieb_angebot.user
    if request.user != vertrieb_angebot.user and not request.user.is_staff:
        return page_not_found(request, Exception())
    user_angebots = VertriebAngebot.objects.filter(user=user)

    ticket_path = os.path.join(settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Tickets/")  # type: ignore

    ticket_files = [
        os.path.join(ticket_path, f"Ticket_{vertrieb_angebot.angebot_id}.pdf")
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
