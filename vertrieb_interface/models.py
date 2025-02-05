# Standard library imports
import datetime
import hashlib
import json
import os
import re
import requests

# Django imports
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

# Third-party imports
from math import ceil
from datetime import timedelta

# Local application/library specific imports
from config.settings import GOOGLE_MAPS_API_KEY
from prices.models import (
    AndereKonfigurationWerte,
    WrGarantiePreise,
    KwpPreise,
    OptionalAccessoriesPreise,
    Sonderrabatt,
    SolarModulePreise,
    WallBoxPreise,
)
from shared.models import TimeStampMixin
from vertrieb_interface.utils import (
    validate_range,
    extract_modulleistungWp,
    sanitize_cache_key,
)

now = timezone.now()
now_german = date_format(now, "DATETIME_FORMAT")
User = get_user_model()

MODULE_NAME_MAP = {
    "Phono Solar PS420M7GFH-18/VNH": "Phono Solar PS420M7GFH-18/VNH",
    "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B": "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B",
}
ACCESSORY_NAME = "leistungsmodul"
#BATT_DICT = {1: 0.6, 2: 0.7, 3: 0.75, 4: 0.8, 5: 0.85, 6: 0.92}
BATT_DICT = {5: 0.6, 7: 0.66, 10: 0.74, 14: 0.79, 15: 0.79, 20: 0.81, 21: 0.81, 25: 0.85, 28: 0.90, 30: 0.92, 35: 0.92,
             42: 0.92}
DEFAULT_BATT_USAGE = 0.35
ANGEBOT_STATUS_CHOICES = [
    ("", ""),
    ("angenommen", "angenommen"),
    ("bekommen", "bekommen"),
    ("in Kontakt", "in Kontakt"),
    ("Kontaktversuch", "Kontaktversuch"),
    ("abgelehnt", "abgelehnt"),
    ("abgelaufen", "abgelaufen"),
    ("on Hold", "on Hold"),
    ("storniert", "storniert"),
]

LEADSTATUS_CHOICES = (
    ("ausstehend", "ausstehend"),
    ("reklamiert", "reklamiert"),
    ("akzeptiert", "akzeptiert"),
    ("abgelehnt", "abgelehnt"),
)
STORNIERUNGSGRUND_CHOICES = (
    (
        "Abweichende Kundenvorstellung zum Thema PVA",
        "Kundenvorstellung zum Thema PVA unterscheidet sich",
    ),
    ("Gebäude ungeeignet", "Das Gebäude ist nicht geeignet"),
    ("Günstigerer Mitbewerber", "Ein Konkurrent bietet günstigere Optionen"),
    ("Investition lohnt sich nicht", "Eine Investition lohnt sich nicht"),
    ("Investition zu teuer", "Die Investitionskosten sind zu hoch"),
    ("Kunde hat kein Interesse mehr", "Der Kunde hat kein Interesse mehr"),
    ("Kunde ist zu alt", "Der Kunde ist nicht mehr interessiert"),
    (
        "Kunde möchte 3-phasige Notstromversorgung",
        "Der Kunde benötigt eine 3-phasige Notstromversorgung",
    ),
    ("Kunde möchte deutsche Produkte", "Der Kunde bevorzugt deutsche Produkte"),
    (
        "Kunde möchte erst später bauen",
        "Der Kunde möchte zu einem späteren Zeitpunkt bauen",
    ),
    ("Kunde möchte Förderung abwarten", "Der Kunde möchte auf Fördermittel warten"),
    (
        "Kunde möchte lokalen Ansprechpartner",
        "Der Kunde wünscht einen Ansprechpartner vor Ort",
    ),
    ("Kunde möchte PVA nur mieten", "Der Kunde möchte die PVA-Anlage nur mieten"),
    ("Kunde war nicht erreichbar", "Der Kunde war nicht erreichbar"),
)
TEXT_FOR_EMAIL = """
                Sehr geehrter Interessent,

                anbei wie besprochen das Angebot im Anhang als PDF-Dokument.

                Bei Fragen stehen wir Ihnen gern jederzeit zur Verfügung!
                

                Wir wünschen Ihnen einen schönen Tag und würden uns über eine positive Rückmeldung freuen
                """

ANREDE_CHOICES = (
    ("Familie", "Familie"),
    ("Firma", "Firma"),
    ("Herr", "Herr"),
    ("Herr Dr.", "Herr Dr."),
    ("Herr Prof.", "Herr Prof."),
    ("Frau", "Frau"),
    ("Frau Prof.", "Frau Prof."),
    ("Frau Dr.", "Frau Dr."),
)
AUSRICHTUNG_CHOICES = (
    ("Sud", "Sud"),
    ("Ost/West", "Ost/West"),
)
KOMPLEX_CHOICES = (
    ("einfach, einfach erreichbar", "einfach, einfach erreichbar"),
    ("einfach, schwer erreichbar", "einfach, schwer erreichbar"),
    ("komplex, einfach erreichbar", "komplex, einfach erreichbar"),
    ("komplex, schwer erreichbar", "komplex, schwer erreichbar"),
    ("sehr komplex", "sehr komplex"),
)

GARANTIE_WR_CHOICES = [
    ("keine", "keine"),
    ("10 Jahre", "10 Jahre"),
    ("15 Jahre", "15 Jahre"),
]


def get_modulleistungWp_from_map(module_name_map):
    result = {}
    for model_name, description in module_name_map.items():
        power = extract_modulleistungWp(description)
        if power:
            result[model_name] = power
    return result


def get_price(model, name):
    model_name = model.__name__
    key = f"{model_name}_{name}"

    sanitized_key = sanitize_cache_key(key)

    price = cache.get(sanitized_key)
    if price is None:
        try:
            price = model.objects.get(name=name).price
        except ObjectDoesNotExist:
            price = 0
        cache.set(sanitized_key, price)
    return price


class LogEntryManager(models.Manager):
    def log_action(
        self, user_id, content_type_id, object_id, object_repr, action_flag, status=None
    ):
        change_message = ""

        if status:
            if status == "angenommen":
                change_message = f"<<Angenommen>>"
            elif status == "bekommen":
                change_message = f"Status geändert zu <<{status}>> "
            elif status == "abgelaufen":
                change_message = f"<<Abgelaufen>>"
            elif status == "in Kontakt":
                change_message = f"Status geändert zu <<{status}>>"
            elif status == "Kontaktversuch":
                change_message = f"Status geändert zu <<{status}>>"
            else:
                change_message = f"Status geändert zu <<{status}>>"

        return self.model.objects.create(
            action_time=timezone.now(),
            user_id=user_id,
            content_type_id=content_type_id,
            object_id=object_id,
            object_repr=object_repr,
            action_flag=action_flag,
            change_message=change_message,
        )


class CustomLogEntry(LogEntry):
    class Meta:
        proxy = True

    objects = LogEntryManager()

    def get_vertrieb_angebot(self):
        from vertrieb_interface.models import VertriebAngebot

        if self.content_type.model_class() == VertriebAngebot:
            try:
                return VertriebAngebot.objects.get(angebot_id=self.object_id)
            except VertriebAngebot.DoesNotExist:
                return VertriebAngebot.objects.filter(angebot_id=self.object_id).first()
        return None

    def get_change_message(self):
        if self.is_addition():
            return f"Ein neues Angebot wurde erstellt"
        elif self.is_change():
            if self.get_vertrieb_angebot() is not None:
                return f"Das Angebot wurde aktualisiert -  {self.change_message}"
            else:
                return f"Das Angebot wurde aktualisiert"
        elif self.is_deletion():
            return f"Das Angebot wurde aktualisiert"
        else:
            return "LogEntry Object"


class VertriebAngebot(TimeStampMixin):
    angebot_id = models.CharField(max_length=255, unique=True, primary_key=True)
    current_date = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_locked = models.BooleanField(default=False)

    #   ZOHO FIELDS
    zoho_id = models.CharField(max_length=255, blank=True, null=True)
    angebot_zoho_id = models.CharField(max_length=255, blank=True, null=True)
    angebot_id_assigned = models.BooleanField(default=False)
    angenommenes_angebot = models.CharField(
        max_length=255, default="", blank=True, null=True
    )
    status = models.CharField(
        choices=ANGEBOT_STATUS_CHOICES,
        default="",
        max_length=255,
        blank=True,
        null=True,
    )
    status_pva = models.CharField(
        default="",
        max_length=255,
        blank=True,
        null=True,
    )
    status_change_field = models.DateTimeField(null=True, blank=True)
    status_change_date = models.CharField(max_length=255, null=True, blank=True)
    telefon_festnetz = models.CharField(max_length=255, blank=True, null=True)
    telefon_mobil = models.CharField(max_length=255, blank=True, null=True)
    zoho_kundennumer = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    text_for_email = models.TextField(blank=True, null=True, default=TEXT_FOR_EMAIL)
    name_display_value = models.CharField(max_length=255, blank=True, null=True)
    vertriebler_display_value = models.CharField(max_length=255, blank=True, null=True)
    vertriebler_id = models.CharField(max_length=255, blank=True, null=True)
    adresse_pva_display_value = models.CharField(max_length=255, blank=True, null=True)
    angebot_bekommen_am = models.CharField(max_length=255, blank=True, null=True)
    anfrage_vom = models.CharField(max_length=255, blank=True, null=True)
    postanschrift_latitude = models.CharField(
        max_length=255, default="00000", blank=True, null=True
    )
    postanschrift_longitude = models.CharField(
        max_length=255, default="00000", blank=True, null=True
    )
    notizen = models.TextField(blank=True, null=True)
    pva_klein = models.CharField(max_length=255, blank=True, null=True)
    b2b_partner = models.CharField(max_length=255, blank=True, null=True)
    name_prefix = models.CharField(max_length=255, blank=True, null=True)
    name_last_name = models.CharField(max_length=255, blank=True, null=True)
    name_suffix = models.CharField(max_length=255, blank=True, null=True)
    name_first_name = models.CharField(max_length=255, blank=True, null=True)
    leadstatus = models.CharField(
        choices=LEADSTATUS_CHOICES, max_length=255, blank=True, null=True
    )
    anfrage_ber = models.CharField(max_length=255, blank=True, null=True)
    empfohlen_von = models.CharField(max_length=255, blank=True, null=True)
    termine_text = models.CharField(max_length=255, blank=True, null=True)
    termine_id = models.CharField(max_length=255, blank=True, null=True)
    ablehnungs_grund = models.CharField(
        choices=STORNIERUNGSGRUND_CHOICES, max_length=255, blank=True, null=True
    )

    anrede = models.CharField(choices=ANREDE_CHOICES, blank=True, max_length=20)
    name = models.CharField(max_length=100, blank=True, default="------")
    vorname_nachname = models.CharField(max_length=100, blank=True, null=True)
    zoho_first_name = models.CharField(max_length=100, blank=True, null=True)
    zoho_last_name = models.CharField(max_length=100, blank=True, null=True)
    firma = models.CharField(max_length=100, blank=True)
    strasse = models.CharField(max_length=100, blank=True)
    ort = models.CharField(max_length=100, blank=True)
    anlagenstandort = models.CharField(max_length=100, blank=True, null=True)

    # Kalkulations
    verbrauch = models.FloatField(
        default=15000, validators=[MinValueValidator(0)]  # type: ignore
    )
    grundpreis = models.FloatField(
        default=9.8, validators=[MinValueValidator(0)]  # type: ignore
    )
    arbeitspreis = models.FloatField(
        default=46.8, validators=[MinValueValidator(0)]  # type: ignore
    )
    prognose = models.FloatField(
        default=5.2, validators=[MinValueValidator(0)]  # type: ignore
    )
    zeitraum = models.PositiveIntegerField(default=15)
    bis10kWp = models.FloatField(
        default=8.20, validators=[MinValueValidator(0)]  # type: ignore
    )
    bis40kWp = models.FloatField(
        default=7.10, validators=[MinValueValidator(0)]  # type: ignore
    )

    benotigte_restenergie = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )

    nutzbare_nutzenergie = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    erzeugte_energie_pro_jahr = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    einspreisevergütung_gesamt = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    abzug_vergutung = models.FloatField(default=0.00, validators=[MinValueValidator(0)])
    Ersparnis = models.FloatField(default=0.00)
    kosten_fur_restenergie = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    Rest_liste = models.TextField(blank=True, null=True)
    Arbeits_liste = models.TextField(blank=True, null=True)

    # Module & Zubehör
    hersteller = models.CharField(
        max_length=100,
        default="Huawei",
    )
    wechselrichter_model = models.CharField(
        max_length=100,
        default="----",
    )
    speicher_model = models.CharField(
        max_length=100,
        default="----",
    )
    smartmeter_model = models.CharField(
        max_length=100,
        default="----",
    )
    gesamtkapazitat = models.PositiveIntegerField(default=0)
    speicher = models.BooleanField(default=False)
    anz_speicher = models.PositiveIntegerField(default=0, validators=[validate_range])
    wandhalterung_fuer_speicher = models.BooleanField(default=False)
    anz_wandhalterung_fuer_speicher = models.PositiveIntegerField(default=0)
    ausrichtung = models.CharField(
        max_length=10, choices=AUSRICHTUNG_CHOICES, default="Ost/West"
    )
    komplex = models.CharField(
        max_length=30, choices=KOMPLEX_CHOICES, default="sehr komplex"
    )

    solar_module = models.CharField(
        max_length=100,
        default="Phono Solar PS420M7GFH-18/VNH",
    )
    modulleistungWp = models.PositiveIntegerField(default=420)
    modulanzahl = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    garantieWR = models.CharField(
        max_length=10, choices=GARANTIE_WR_CHOICES, default="10 Jahre"
    )
    # Zubehör
    elwa = models.BooleanField(default=False)
    thor = models.BooleanField(default=False)
    heizstab = models.BooleanField(default=False)
    notstrom = models.BooleanField(default=False)
    optimizer = models.BooleanField(default=False)
    anzOptimizer = models.PositiveIntegerField(default=0)
    apzFeld = models.BooleanField(default=False)
    zaehlerschrank = models.BooleanField(default=False)
    potentialausgleich = models.BooleanField(default=False)
    beta_platte = models.BooleanField(default=False)
    metall_ziegel = models.BooleanField(default=False)
    prefa_befestigung = models.BooleanField(default=False)
    midZaehler = models.PositiveIntegerField(default=0)
    wallbox = models.BooleanField(default=False)
    wallboxtyp = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    wallbox_anzahl = models.PositiveIntegerField(default=0)
    kabelanschluss = models.FloatField(
        default=10.0, validators=[MinValueValidator(0)], blank=True, null=True
    )
    geruestKunde = models.BooleanField(default=False)
    geruestOeffentlich = models.BooleanField(default=False)
    smartDongleLte = models.BooleanField(default=False)
    dachhakenKunde = models.BooleanField(default=False)
    indiv_price_included = models.BooleanField(default=False)
    indiv_price = models.FloatField(default=0.00, validators=[MinValueValidator(0)])
    zahlungsbedingungen = models.CharField(
        max_length=25,
        blank=True,
        null=True,
    )
    rabatt = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    sonderrabatt_included = models.BooleanField(default=False)
    sonderrabatt = models.CharField(
        max_length=100,
        default="----",
    )
    ausweisung_rabatt = models.BooleanField(default=False)
    genehmigung_rabatt = models.BooleanField(default=False)

    # Result Prices :
    solar_module_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    batteriespeicher_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    smartmeter_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    wallbox_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    notstrom_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    optimizer_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )

    angebotsumme = models.FloatField(default=0.00, validators=[MinValueValidator(0)])
    rabattsumme = models.FloatField(default=0.00, validators=[MinValueValidator(0)])

    # Finanzierung
    finanzierung = models.BooleanField(default=False)
    anzahlung = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    nettokreditbetrag = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    monatliche_rate = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    laufzeit = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    sollzinssatz = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    effektiver_zins = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    gesamtkreditbetrag = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )

    # Files and other fields:
    datenblatter_solar_module = models.BooleanField(default=False)
    datenblatter_speichermodule = models.BooleanField(default=False)
    datenblatter_smartmeter = models.BooleanField(default=False)
    datenblatter_wechselrichter = models.BooleanField(default=False)
    datenblatter_wallbox = models.BooleanField(default=False)
    datenblatter_backup_box = models.BooleanField(default=False)
    datenblatter_optimizer = models.BooleanField(default=False)
    profile_foto = models.BinaryField(blank=True, null=True)
    angebot_pdf = models.BinaryField(blank=True, null=True)
    calc_pdf = models.BinaryField(blank=True, null=True)
    calc_graph_img = models.ImageField(null=True, blank=True)
    ag_data = models.TextField(blank=True)
    ag_fetched_data = models.TextField(blank=True, null=True)
    countdown_on = models.BooleanField(default=False)

    def get_optional_accessory_price(self, name):
        return float(OptionalAccessoriesPreise.objects.get(name=name).price)

    def get_module_preis(self, name):
        return float(SolarModulePreise.objects.get(name=name).price)

    def get_module_garantie(self, name):
        try:
            out = str(SolarModulePreise.objects.get(name=name).module_garantie)
        except:
            out = ""
        return out

    def get_wr_garantie_preis(self, name):
        return float(WrGarantiePreise.objects.get(name=name).price)

    def get_leistungs_garantie(self, name):
        try:
            out = str(SolarModulePreise.objects.get(name=name).leistungs_garantie)
        except:
            out = ""
        return out

    def get_wallbox_text(self, name):
        try:
            out = str(WallBoxPreise.objects.get(name=name).pdf_text)
        except:
            out = ""
        return out

    def save(self, *args, **kwargs):
        if not self.angebot_id:
            self.angebot_id = self.generate_angebot_id()
            action_flag = ADDITION
        else:
            action_flag = CHANGE


        self.modulleistungWp = self.extract_modulleistungWp_from_name
        self.wallbox_angebot_price = self.full_wallbox_preis
        self.notstrom_angebot_price = self.get_optional_accessory_price("backup_box")
        self.optimizer_angebot_price = float(self.full_optimizer_preis)
        self.name = self.swap_name_order
        self.name_display_value = self.swap_name_order_PDF
        self.zoho_kundennumer = self.kundennumer_finder
        self.batteriespeicher_angebot_price = self.batteriespeicher_preis
        self.smartmeter_angebot_price = self.smartmeter_preis
        tmpSumme, tmpRabatt = self.angebots_summe
        self.angebotsumme = round(tmpSumme, 2)
        self.rabattsumme = round(tmpRabatt, 2)
        self.anfrage_vom = self.get_current_date_formatted
        self.benotigte_restenergie = self.restenergie
        self.nutzbare_nutzenergie = self.nutz_energie
        self.erzeugte_energie_pro_jahr = self.erzeugte_energie
        self.einspreisevergütung_gesamt = self.einsp_verg
        self.abzug_vergutung = self.abzug
        self.Ersparnis = self.ersparnis
        self.kosten_fur_restenergie = self.kosten_rest_energie
        self.ag_data = self.data
        self.Rest_liste = self.rest_liste
        self.Arbeits_liste = self.arbeits_liste
        self.nettokreditbetrag = self.get_nettokreditbetrag
        super(VertriebAngebot, self).save(*args, **kwargs)

        CustomLogEntry.objects.log_action(
            user_id=self.user_id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.pk,
            object_repr=str(self.angebot_id),
            action_flag=action_flag,
        )

    def __str__(self) -> str:
        return f"{self.angebot_id}"

    def generate_angebot_id(self):
        if self.user_id:
            user = User.objects.get(id=self.user.pk)
            kurz = user.kuerzel  # Assuming 'kuerzel' is an attribute of User
            current_datetime = datetime.datetime.now()
            return f"AN-{kurz}{current_datetime.strftime('%d%m%Y-%H%M%S')}"
        else:
            # Return a default ID
            current_datetime = datetime.datetime.now()
            return f"AN-DEFAULT{current_datetime.strftime('%d%m%Y-%H%M%S')}"

    def get_absolute_url(self):
        return reverse("edit_angebot", args=[str(self.angebot_id)])

    def delete(self, *args, **kwargs):
        # Log deletion before actually deleting
        CustomLogEntry.objects.log_action(
            user_id=self.user_id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.pk,
            object_repr=str(self),
            action_flag=DELETION,
        )
        super().delete(*args, **kwargs)

    @property
    def get_current_date_formatted(self):
        if self.anfrage_vom == None or self.anfrage_vom == "":
            current_datetime = datetime.datetime.now()
            self.anfrage_vom = current_datetime.strftime("%d-%b-%Y")
            return current_datetime.strftime("%d-%b-%Y")
        return self.anfrage_vom

    @property
    def firma_case(self):
        if self.anrede == "Firma":
            self.name_first_name = ""
            return self.name_last_name
        else:
            return self.name

    @property
    def assign_status_change_field(self):
        status_change_field = timezone.localtime(timezone.now())
        return status_change_field

    def countdown(self):
        if self.status_change_field:
            status_change_datetime = self.status_change_field

            delta = timezone.now() - status_change_datetime
            # get the difference in time

            # Check that status_change_field is within the past 14 days
            if delta.days < 0 or delta.days > 14:
                return None

            total_seconds = (
                14 * 24 * 60 * 60 - delta.total_seconds()
            )  # convert the difference to seconds

            # calculate days, hours, minutes
            days, remaining_seconds = divmod(total_seconds, 60 * 60 * 24)
            hours, remaining_seconds = divmod(remaining_seconds, 60 * 60)
            minutes = remaining_seconds // 60

            if total_seconds <= 0:
                return "0 days, 0 hours, 0 minutes"

            return f"{int(days)} Tage, {int(hours)} Stunde, {int(minutes)} Minute"
        else:
            return None

    @property
    def swap_name_order(self):
        if self.anrede == "Firma":
            parts = self.name_last_name
        elif self.anrede == "Familie":
            parts = self.name_last_name
        else:
            if self.name_suffix:
                parts = (
                    str(self.name_last_name)
                    + ", "
                    + str(self.name_suffix)
                    + " "
                    + str(self.name_first_name)
                )
            else:
                parts = str(self.name_last_name) + ", " + str(self.name_first_name)
        return str(parts)

    @property
    def swap_name_order_PDF(self):
        if self.anrede == "Firma":
            parts = self.name_last_name
        elif self.anrede == "Familie":
            parts = self.name_last_name
        else:
            if self.name_suffix:
                parts = (
                    str(self.name_suffix)
                    + " "
                    + str(self.name_first_name)
                    + " "
                    + str(self.name_last_name)
                )
            else:
                parts = str(self.name_first_name) + " " + str(self.name_last_name)
        return str(parts)

    @property
    def kundennumer_finder(self):
        if self.zoho_kundennumer:
            return self.zoho_kundennumer

        if not self.zoho_id:
            return ""

        try:
            data = json.loads(
                self.user.zoho_data_text
                or '[{"zoho_id": "default", "zoho_kundennumer": "default"}]'
            )
        except json.JSONDecodeError:
            return ""

        zoho_id = str(self.zoho_id)
        return next(
            (
                item["zoho_kundennumer"]
                for item in data
                if item.get("zoho_id") == zoho_id
            ),
            "",
        )


    @property
    def get_building_insights(
        self, latitude=None, longitude=None, requiredQuality="HIGH"
    ):
        # Replace with your Solar API key if different
        if self.postanschrift_latitude and self.postanschrift_longitude:
            latitude = float(self.postanschrift_latitude)
            longitude = float(self.postanschrift_longitude)
        else:
            latitude, longitude = self.coordinates_extractor
        url = f"https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude={latitude}&location.longitude={longitude}&requiredQuality={requiredQuality}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        return response.json()

    @property
    def google_maps_url(self):
        if self.postanschrift_latitude and self.postanschrift_longitude:
            latitude = float(self.postanschrift_latitude)
            longitude = float(self.postanschrift_longitude)
            maps_url = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=14/{latitude}/{longitude}"
            return maps_url
        elif not self.postanschrift_latitude or not self.postanschrift_longitude:
            latitude, longitude = self.coordinates_extractor
            maps_url = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=14/{latitude}/{longitude}"
            return maps_url
        else:
            return ""

    @property
    def get_vertribler(self):
        return f"{self.user.first_name} {self.user.last_name} \nMobil: {self.user.phone}\nEmail: {self.user.email}"  # type: ignore

    @property
    def vertrieb_abk(self):
        return f"{self.user.kuerzel}"  # type: ignore

    @property
    def angebot_gultig(self):
        current_date = datetime.datetime.now()
        frist = current_date + timedelta(days=14)
        return frist.strftime("%d.%m.%Y")

    """

    CALCULATING   KUNDEN DATAS  

    """

    @property
    def full_adresse(self):
        return f"{self.strasse}\n{self.ort}"

    @property
    def anlagen_standort(self):
        if self.anlagenstandort:
            return self.anlagenstandort
        else:
            return f"{self.strasse}, {self.ort}"

    @property
    def extract_modulleistungWp_from_name(self):
        match = re.search(r"(\d+)", str(self.solar_module))
        if match:
            return int(match.group(1))
        return 420


    @property
    def leistungsmodul_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="leistungsmodul").price)

    @property
    def stromgrundpreis_gesamt(self):
        return round(float(self.grundpreis) * 12 * int(self.zeitraum), 2)

    @staticmethod
    def priceInflation(pricePerYear, increasePerYear, years):
        sumPrice = 0
        priceList = []
        for i in range(years):
            sumPrice += pricePerYear
            priceList.append(sumPrice)
            pricePerYear = pricePerYear * (1.0 + increasePerYear)
        return sumPrice, priceList

    def get_arbeitspreis_and_list(self):
        if not hasattr(self, "_arbeitspreis_and_list"):
            try:
                if float(self.verbrauch):
                    self._arbeitspreis_and_list = self.priceInflation(
                        float(self.arbeitspreis) / 100 * float(self.verbrauch),
                        float(self.prognose) / 100,
                        int(self.zeitraum),
                    )

            except:
                self.verbrauch = 15000.0
                self._arbeitspreis_and_list = self.priceInflation(
                    float(self.arbeitspreis) / 100 * float(self.verbrauch),
                    float(self.prognose) / 100,
                    int(self.zeitraum),
                )
        return self._arbeitspreis_and_list

    @property
    def arbeitspreis_gesamt(self):
        arb_ges, _ = self.get_arbeitspreis_and_list()
        return round(arb_ges, 2)

    @property
    def arbeits_liste(self):
        _, arb_liste = self.get_arbeitspreis_and_list()
        return arb_liste

    @property
    def erzProJahr(self):
        direction_map = {"Sud": "erzeugung_sued", "Ost/West": "erzeugung_ost_west"}
        direction = str(self.ausrichtung)
        if direction in direction_map:
            return AndereKonfigurationWerte.objects.get(
                name=direction_map[direction]
            ).value
        else:
            return 0.00


    @property
    def get_komplexity(self):
        complexity_map = {
            "einfach, einfach erreichbar": "einfach_einfach_erreichbar",
            "einfach, schwer erreichbar": "einfach_schwer_erreichbar",
            "komplex, einfach erreichbar": "komplex_einfach_erreichbar",
            "komplex, schwer erreichbar": "komplex_schwer_erreichbar",
            "sehr komplex": "sehr_komplex",
        }
        complexity = str(self.komplex)
        if complexity in complexity_map:
            return AndereKonfigurationWerte.objects.get(
                name=complexity_map[complexity]
            ).value
        else:
            return 0.00

    """

    CALCULATING   SOLAR MODULE PARAMETERS  

    """

    @staticmethod
    def get_values():
        return {obj.name: obj.zuschlag for obj in SolarModulePreise.objects.all()}

    @staticmethod
    def get_prices():
        return {obj.name: obj.price for obj in OptionalAccessoriesPreise.objects.all()}

    @staticmethod
    def get_module_prices():
        return {obj.name: obj.price for obj in SolarModulePreise.objects.all()}

    def calculate_price(self, model, name, multiplier):
        try:
            multiplier = int(multiplier)
        except ValueError:
            multiplier = 0
        price = get_price(model, name)
        return price * multiplier

    @property
    def modulleistung_price(self):
        prices = self.get_prices()
        return float(prices[ACCESSORY_NAME])

    @property
    def elwa_price(self):
        prices = self.get_prices()
        return float(prices["elwa_2"])

    @property
    def thor_price(self):
        prices = self.get_prices()
        return float(prices["ac_thor_3_kw"])

    @property
    def heizstab_price(self):
        prices = self.get_prices()
        return float(prices["heizstab"])

    @property
    def solar_module_gesamt_preis(self):
        module_prices = self.get_module_prices()
        module_name = (
            self.solar_module if self.solar_module else "Phono Solar PS420M7GFH-18/VNH"
        )
        try:
            return float(module_prices[module_name]) * int(self.modulanzahl)
        except KeyError:
            # handle the error, maybe return a default value or raise a more descriptive error
            return 0.0

    @property
    def beta_platte_preis(self):
        limits = [7, 11, 15, 19, 23, 27, 30]
        kwp = min(30, self.modulsumme_kWp)
        kwpUpper = min(upper for upper in limits if upper >= kwp)
        namePlatte = "BetaPlatte" + str(kwpUpper)
        beta_preis = float(KwpPreise.objects.get(name=namePlatte).price)
        return beta_preis

    @property
    def metall_ziegel_preis(self):
        limits = [7, 11, 15, 19, 23, 27, 30]
        kwp = min(30, self.modulsumme_kWp)
        kwpUpper = min(upper for upper in limits if upper >= kwp)
        nameZiegel = "MetallZiegel" + str(kwpUpper)
        ziegel_preis = float(KwpPreise.objects.get(name=nameZiegel).price)
        return ziegel_preis

    @property
    def prefa_befestigung_preis(self):
        prefa_preis = OptionalAccessoriesPreise.objects.get(name="prefa_befestigung").price * self.modulanzahl
        return prefa_preis
    @property
    def wandhalterung_fuer_speicher_preis(self):
        wandhalterung_preis = 0
        if self.anz_wandhalterung_fuer_speicher != 0:
            anz_wandhalterung_fuer_speicher = int(self.anz_wandhalterung_fuer_speicher)
            wandhalterung_preis = self.calculate_price(
                OptionalAccessoriesPreise,
                "wandhalterung_fuer_speicher",
                anz_wandhalterung_fuer_speicher,
            )

            return wandhalterung_preis

    @property
    def midZaehler_preis(self):
        midZaehler_preis = 0
        if self.midZaehler != 0:
            anz_midZaehler = int(self.midZaehler)
            midZaehler_preis = self.calculate_price(
                OptionalAccessoriesPreise,
                "mid_zaehler",
                anz_midZaehler,
            )
            return midZaehler_preis

    @property
    def batteriespeicher_preis(self):
        batterieDict = {"LUNA 2000-5-S0": "batteriemodul_huawei5", "LUNA 2000-7-S1": "batteriemodul_huawei7",
                        "Vitocharge VX3 PV-Stromspeicher": "batteriemodul_viessmann"}
        leistModDict = {"LUNA 2000-5-S0": True, "LUNA 2000-7-S1": True, "Vitocharge VX3 PV-Stromspeicher": False}
        batteriePreis = 0
        if self.anz_speicher != 0:
            anz_speicher = int(self.anz_speicher)
            leistungsmodulNotwendig = leistModDict.get(self.speicher_model)
            batterieDatensatz = batterieDict.get(self.speicher_model)
            # Kein angenommenes Angebot oder angenommenes Angebot hatte keinen Speicher
            if batterieDatensatz is not None:
                batteriePreis = self.calculate_price(OptionalAccessoriesPreise, batterieDatensatz, anz_speicher)
                if leistungsmodulNotwendig:
                    batteriePreis = float(batteriePreis) + ceil(anz_speicher / 3) * float(self.leistungsmodul_preis)
                # Falls mehr als 6 Speichermodule bei Huawei 7 eventuell Zusatzwechselrichter notwendig wegen fehlenden Steckplätzen
                if self.modulsumme_kWp < 25.0 and self.speicher_model == "LUNA 2000-7-S1" and anz_speicher > 6:
                    batteriePreis += self.get_optional_accessory_price("zusatzwechselrichter")
                return batteriePreis
        return batteriePreis

    @property
    def smartmeter_preis(self):
        smartmeterPreis = 0
        if self.smartmeter_model == "Smart Power Sensor DTSU666H":
            smartmeterPreis = self.calculate_price(
                    OptionalAccessoriesPreise, "smartmeter_dtsu", 1
                )
        elif self.smartmeter_model == "EMMA-A02":
            smartmeterPreis = self.calculate_price(
                OptionalAccessoriesPreise, "smartmeter_emma", 1
            )
        elif self.smartmeter_model == "Viessmann Energiezähler":
            smartmeterPreis = self.calculate_price(
                OptionalAccessoriesPreise, "smartmeter_viessmann", 1
            )
        return smartmeterPreis

    @property
    def modulsumme_kWp(self):
        return self.modulleistungWp * self.modulanzahl / 1000


    @property
    def get_nettokreditbetrag(self):
        return self.angebotsumme - self.anzahlung

    @property
    def get_zuschlag(self):
        # Fetch all the values
        values = self.get_values()

        # Check if 'self.solar_module' is not None, else assign the default module name
        module_name = (self.solar_module if self.solar_module else ("Phono Solar PS420M7GFH-18/VNH"))
        # Return value based on module_name
        return float(values.get(module_name))


    @property
    def nutz_energie(self):
        nutzEnergie = float(self.verbrauch)
        if self.erzeugte_energie < nutzEnergie:
            nutzEnergie = float(self.erzProJahr) * float(self.modulsumme_kWp)
        if self.anz_speicher != 0:
            if self.speicher_model == "LUNA 2000-7-S1":
                kwh = self.anz_speicher * 7
            else:
                kwh = self.anz_speicher * 5
            # Limitierung bis 6 Speichermodule, danach pauschal kein noch besserer Eigenverbrauch
            nutzEnergie = nutzEnergie * BATT_DICT[min(kwh,42)]
        else:
            nutzEnergie = nutzEnergie * DEFAULT_BATT_USAGE
        return round(nutzEnergie, 2)

    @property
    def restenergie(self):
        rest = 0

        if float(self.verbrauch):
            rest += float(self.verbrauch) - float(self.nutz_energie)
            return rest
        else:
            return 0

    @property
    def rest_strom_preis(self):
        reststromPreis, _ = self.priceInflation(
            float(self.arbeitspreis) / 100 * float(self.restenergie),
            float(self.prognose) / 100,
            self.zeitraum,
        )
        return round(reststromPreis, 2)

    @property
    def strom_ohne(self):
        return float(self.stromgrundpreis_gesamt) + float(self.arbeitspreis_gesamt)

    @property
    def kosten_rest_energie(self):
        return self.rest_strom_preis + self.stromgrundpreis_gesamt

    @property
    def einsp_pro_jahr(self):
        if self.modulsumme_kWp <= 10:
            return float(self.bis10kWp) * 0.01 * self.einsp_energie
            # return float(self.bis10kWp) * 0.01 * (10 / self.modulsumme_kWp)
        else:
            klZehn = float(self.bis10kWp) * 0.01 * (10 / self.modulsumme_kWp)
            grZehn = (
                float(self.bis40kWp)
                * 0.01
                * (self.modulsumme_kWp - 10)
                / self.modulsumme_kWp
            )
            return (klZehn + grZehn) * self.einsp_energie

    @property
    def erzeugte_energie(self):
        return round(float(self.erzProJahr) * float(self.modulsumme_kWp), 2)

    @property
    def einsp_energie(self):
        return self.erzeugte_energie - self.nutz_energie

    @property
    def einsp_verg(self):
        return round(self.einsp_pro_jahr * self.zeitraum, 2)

    """

    CALCULATING   WALLBOX  

    """

    @property
    def wallbox_anzahl_pdf(self):
        if self.wallbox_anzahl and self.wallbox_anzahl > 3:
            raise ValueError(
                "Achtung, mehr als 3 Wallboxen ausgewählt, bitte Preise für Harvi & Hub bzw. Power Boost überprüfen."
            )
        return (
            "\n1\n1"
            if "Zappi" in str(self.wallboxtyp)
            else "\n1" if "Power Boost" in str(self.wallboxtyp) else "\n1"
        )

    @property
    def wallbox_kabel_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="kabelpreis").price)

    @property
    def optimizer_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="optimizer").price)

    @property
    def optimizer_full_preis(self):
        return self.anzOptimizer * self.optimizer_preis


    """

    CALCULATING   ANGEBOT SUMME  

    """

    @property
    def full_optimizer_preis(self):
        return self.anzOptimizer * self.get_optional_accessory_price("optimizer")

    @property
    def full_wallbox_preis(self):
        if self.wallbox_anzahl:
            preis = float(WallBoxPreise.objects.get(name=str(self.wallboxtyp)).price)
            preis *= self.wallbox_anzahl
            if self.kabelanschluss and self.kabelanschluss >= 10:
                preis += (self.kabelanschluss - 10) * self.get_optional_accessory_price(
                    "kabelpreis"
                )
            return preis
        else:
            return 0.00

    @property
    def full_accessories_price(self):
        accessories_price = 0
        if self.full_optimizer_preis:
            accessories_price += float(self.full_optimizer_preis)
        if self.full_wallbox_preis:
            accessories_price += float(self.full_wallbox_preis)
        if self.batteriespeicher_angebot_price:
            accessories_price += float(self.batteriespeicher_angebot_price)
        if self.smartmeter_angebot_price:
            accessories_price += float(self.smartmeter_angebot_price)
        if self.notstrom:
            accessories_price += float(self.get_optional_accessory_price("backup_box"))
        if self.smartDongleLte:
            accessories_price += float(self.get_optional_accessory_price("smartDongleLte"))
        if self.midZaehler > 0:
            accessories_price += float(self.midZaehler_preis)
        if self.apzFeld:
            accessories_price += float(self.get_optional_accessory_price("apzFeld"))
        if self.zaehlerschrank:
            accessories_price += float(self.get_optional_accessory_price("zaehlerschrank"))
        if self.potentialausgleich:
            accessories_price += float(self.get_optional_accessory_price("potentialausgleich"))
        if self.beta_platte:
            accessories_price += float(self.beta_platte_preis)
        if self.metall_ziegel:
            accessories_price += float(self.metall_ziegel_preis)
        if self.prefa_befestigung:
            accessories_price += float(self.prefa_befestigung_preis)
        if self.wandhalterung_fuer_speicher_preis:
            accessories_price += float(self.wandhalterung_fuer_speicher_preis)
        if self.elwa:
            accessories_price += float(self.elwa_price)
        if self.thor:
            accessories_price += float(self.thor_price)
        if self.heizstab:
            accessories_price += float(self.heizstab_price)
        return accessories_price

    @property
    def angebots_summe(self):
        def get_price(prefix, kw):
            name = prefix + str(kw)
            return (float(KwpPreise.objects.get(name=name).price)) * float(
                self.get_zuschlag
            )

        def get_garantie_price(kw, years):
            name = f"garantie{kw}_{years}"
            return float(WrGarantiePreise.objects.get(name=name).price)

        limits = [5, 7, 10, 12, 15, 20, 25, 30]
        ranges = ([(0, limits[0])]
            + list(zip(limits, limits[1:]))
            + [(limits[-1], float("30"))]
        )

        kwp = min(30, self.modulsumme_kWp)
        angebotsSumme = sum(
            (min(self.modulsumme_kWp, upper) - lower) * get_price("Preis", upper)
            for lower, upper in ranges
            if lower < kwp
        )

        if self.user.typ == "Evolti":  # type: ignore
            angebotsSumme *= 1.05

        angebotsSumme *= float(self.get_komplexity)
        angebotsSumme += float(self.full_accessories_price)

        if self.hersteller == "Huawei" and self.garantieWR != "keine":
            garantie_faktor = float(AndereKonfigurationWerte.objects.get(name="garantiefaktor").value)
            garantie_years = int(self.garantieWR.split(" ")[0])
            garantie_kw = next(
                kw
                for kw in [3, 4, 5, 6, 8, 10, 15, 16, 20, 25, 30]
                if kwp <= kw
            )
            angebotsSumme += get_garantie_price(garantie_kw, garantie_years) * garantie_faktor

        if self.indiv_price_included:
            if self.user.typ == "Evolti":  # type: ignore
                angebotsSumme *= 1.07
            angebotsSumme = self.indiv_price

        rabatt = angebotsSumme * (self.rabatt/100)
        angebotsSumme *= (1-(self.rabatt/100))

        # Sonderrabatte
        if self.sonderrabatt_included and Sonderrabatt.objects.all().exists():
            angebotsSumme *= (1-(float(Sonderrabatt.objects.get(name=self.sonderrabatt).prozentsatz)/100))
            angebotsSumme -= float(Sonderrabatt.objects.get(name=self.sonderrabatt).fixbetrag)

        userAufschlag = float(self.user.users_aufschlag) / 100 + 1  # type: ignore
        angebotsSumme *= userAufschlag
        # Abzug Selbstleistungen nach Rabattierung
        if self.geruestKunde:
            angebotsSumme -= float(self.get_optional_accessory_price("geruestKunde"))
            rabatt += float(self.get_optional_accessory_price("geruestKunde"))
        elif self.geruestOeffentlich:
            angebotsSumme += float(self.get_optional_accessory_price("geruestOeffentlich"))
        if self.dachhakenKunde:
            angebotsSumme -= float(self.get_optional_accessory_price("dachhakenKunde"))
            rabatt += float(self.get_optional_accessory_price("dachhakenKunde"))
        # Aufpreis Finanzierung nach Rabattierung
        if self.finanzierung:
            angebotsSumme += 300
        return angebotsSumme, rabatt


    @property
    def kosten_pva(self):
        return float(self.angebots_summe[0]) * float(
            1 + AndereKonfigurationWerte.objects.get(name="steuersatz").value
        )

    @property
    def abzug(self):
        res = 0.0
        if (
            self.kosten_pva
            and self.rest_strom_preis
            and self.stromgrundpreis_gesamt
            and self.einsp_verg
        ):
            res += (
                self.kosten_pva
                + self.rest_strom_preis
                + self.stromgrundpreis_gesamt
                - self.einsp_verg
            )
        return round(res, 2)

    @property
    def ersparnis(self):
        ersp = float(self.arbeitspreis_gesamt) - (
            float(self.kosten_pva)
            + float(self.rest_strom_preis)
            - float(self.einsp_verg)
        )
        return round(ersp, 2)

    @property
    def rest_liste(self):
        restenergie = float(self.verbrauch) - self.nutz_energie
        _, restListe = self.priceInflation(
            float(self.arbeitspreis) / 100 * restenergie,
            float(self.prognose) / 100,
            self.zeitraum,
        )
        for i in range(self.zeitraum):
            self.arbeits_liste[i] += float(self.grundpreis) * 12 * (i + 1)
            restListe[i] += float(self.grundpreis) * 12 * (i + 1)
            restListe[i] += self.kosten_pva
            restListe[i] -= self.einsp_pro_jahr * (i + 1)
        return restListe

    @property
    def data(self):
        dt = {
            "firma": self.firma,
            "anrede": self.anrede,
            "kunde": self.name_display_value,
            "adresse": self.full_adresse,
            "vertriebler": str(self.get_vertribler),
            "vertriebAbk": self.vertrieb_abk,
            "gueltig": self.angebot_gultig,
            "module": self.solar_module,
            "wpModule": self.modulleistungWp,
            "anzModule": self.modulanzahl,
            "produktGarantie": self.get_module_garantie(self.solar_module),
            "leistungsGarantie": self.get_leistungs_garantie(self.solar_module),
            "kWp": self.modulsumme_kWp,
            "kWpOhneRundung": self.modulsumme_kWp,
            "standort": self.anlagen_standort,
            "garantieJahre": self.garantieWR,
            "batterieVorh": self.batteriespeicher_preis,
            "batterieModell": self.speicher_model,
            "smartmeterModell": self.smartmeter_model,
            "wandhalterungSpeicher": self.wandhalterung_fuer_speicher,
            "anzWandhalterungSpeicher": self.anz_wandhalterung_fuer_speicher,
            "wandhalterungSpeicherPreis": self.wandhalterung_fuer_speicher_preis,
            "batterieAnz": self.anz_speicher,
            "wallboxVorh": self.full_wallbox_preis,
            "wallboxTyp": self.wallboxtyp,
            "wallboxText": self.get_wallbox_text(self.wallboxtyp),
            "wallboxAnz": self.wallbox_anzahl,
            "optionVorh": self.notstrom,
            "elwa": self.elwa,
            "thor": self.thor,
            "midZaehler": self.midZaehler,
            "apzFeld": self.apzFeld,
            "zaehlerschrank": self.zaehlerschrank,
            "potentialausgleich": self.potentialausgleich,
            "geruestKunde": self.geruestKunde,
            "geruestOeffentlich": self.geruestOeffentlich,
            "dachhakenKunde": self.dachhakenKunde,
            "betaPlatte": self.beta_platte,
            "metallZiegel": self.metall_ziegel,
            "prefaBefestigung": self.prefa_befestigung,
            "heizstab": self.heizstab,
            "smartDongleLte": self.smartDongleLte,
            "optimierer": self.optimizer,
            "anzOptimierer": self.anzOptimizer,
            "notstrom": self.notstrom,
            "solarModulePreis": self.solar_module_gesamt_preis,
            "wallboxPreis": self.full_wallbox_preis,
            "notstromPreis": self.get_optional_accessory_price("backup_box"),
            "batterieSpeicherPreis": self.batteriespeicher_preis,
            "gesamtOptimizerPreis": self.full_optimizer_preis,
            "zahlungs_bedingungen": self.zahlungsbedingungen,
            "rabatt": self.rabatt,
            "rabattsumme": self.rabattsumme,
            "genehmigung_rabatt": self.genehmigung_rabatt,
            "ausweisung_rabatt": self.ausweisung_rabatt,
            "angebotssumme": self.angebotsumme,
            "steuersatz": float(
                AndereKonfigurationWerte.objects.get(name="steuersatz").value
            ),
            "finanzierung": self.finanzierung,
            "anzahlung": self.anzahlung,
            "nettokreditbetrag": self.nettokreditbetrag,
            "monatliche_rate": self.monatliche_rate,
            "laufzeit": self.laufzeit,
            "sollzinssatz": self.sollzinssatz,
            "effektiver_zins": self.effektiver_zins,
            "gesamtkreditbetrag": self.gesamtkreditbetrag,
            "debug": False,
            "hersteller": self.hersteller,
            "version": 1.0,
            "stromverbrauch": self.verbrauch,
            "grundpreis": self.grundpreis,
            "arbeitspreis": self.arbeitspreis,
            "prognose": self.prognose,
            "zeitraum": int(self.zeitraum),
            "bis10kWp": float(self.bis10kWp),
            "10bis40kWp": float(self.bis40kWp),
            "ausrichtung": self.ausrichtung,
            "erzeugungSued": self.erzProJahr,
            "erzeugungOstWest": self.erzProJahr,
            "grundpreisGes": self.stromgrundpreis_gesamt,
            "arbeitspreisGes": self.arbeitspreis_gesamt,
            "erzeugteEnergie": self.erzeugte_energie,
            "nutzEnergie": self.nutzbare_nutzenergie,
            "restenergie": self.restenergie,
            "reststromPreis": self.rest_strom_preis,
            "einspVerg": self.einsp_verg,
            "kostenPVA": self.kosten_pva,
            "ersparnis": self.ersparnis,
            "arbeitsListe": self.arbeits_liste,
            "restListe": self.rest_liste,
        }
        return dt


class VertriebTicket(TimeStampMixin):
    ticket_id = models.CharField(max_length=255, unique=True, primary_key=True)
    current_date = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_locked = models.BooleanField(default=False)

    #   ZOHO FIELDS
    zoho_id = models.CharField(max_length=255, blank=True, null=True)
    angebot_zoho_id = models.CharField(max_length=255, blank=True, null=True)
    angebot_id_assigned = models.BooleanField(default=False)
    angenommenes_angebot = models.CharField(
        max_length=255, default="", blank=True, null=True
    )
    status = models.CharField(
        choices=ANGEBOT_STATUS_CHOICES,
        default="",
        max_length=255,
        blank=True,
        null=True,
    )
    status_pva = models.CharField(
        default="",
        max_length=255,
        blank=True,
        null=True,
    )
    status_change_field = models.DateTimeField(null=True, blank=True)
    status_change_date = models.CharField(max_length=255, null=True, blank=True)
    telefon_festnetz = models.CharField(max_length=255, blank=True, null=True)
    telefon_mobil = models.CharField(max_length=255, blank=True, null=True)
    zoho_kundennumer = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    text_for_email = models.TextField(blank=True, null=True, default=TEXT_FOR_EMAIL)
    name_display_value = models.CharField(max_length=255, blank=True, null=True)
    vertriebler_display_value = models.CharField(max_length=255, blank=True, null=True)
    vertriebler_id = models.CharField(max_length=255, blank=True, null=True)
    adresse_pva_display_value = models.CharField(max_length=255, blank=True, null=True)
    angebot_bekommen_am = models.CharField(max_length=255, blank=True, null=True)
    anfrage_vom = models.CharField(max_length=255, blank=True, null=True)
    postanschrift_latitude = models.CharField(
        max_length=255, default="00000", blank=True, null=True
    )
    postanschrift_longitude = models.CharField(
        max_length=255, default="00000", blank=True, null=True
    )
    notizen = models.TextField(blank=True, null=True)
    pva_klein = models.CharField(max_length=255, blank=True, null=True)
    name_prefix = models.CharField(max_length=255, blank=True, null=True)
    name_last_name = models.CharField(max_length=255, blank=True, null=True)
    name_suffix = models.CharField(max_length=255, blank=True, null=True)
    name_first_name = models.CharField(max_length=255, blank=True, null=True)

    anrede = models.CharField(choices=ANREDE_CHOICES, blank=True, max_length=20)
    name = models.CharField(max_length=100, blank=True, default="------")
    vorname_nachname = models.CharField(max_length=100, blank=True, null=True)
    zoho_first_name = models.CharField(max_length=100, blank=True, null=True)
    zoho_last_name = models.CharField(max_length=100, blank=True, null=True)
    firma = models.CharField(max_length=100, blank=True)
    strasse = models.CharField(max_length=100, blank=True)
    ort = models.CharField(max_length=100, blank=True)
    anlagenstandort = models.CharField(max_length=100, blank=True, null=True)


    # Module & Zubehör

    speicher_model = models.CharField(
        max_length=100,
        default="----",
    )
    smartmeter_model = models.CharField(
        max_length=100,
        default="----",
    )
    gesamtkapazitat = models.PositiveIntegerField(default=0)
    speicher = models.BooleanField(default=False)
    anz_speicher = models.IntegerField(default=0, validators=[validate_range])
    wandhalterung_fuer_speicher = models.BooleanField(default=False)
    anz_wandhalterung_fuer_speicher = models.PositiveIntegerField(default=0)
    solar_module = models.CharField(
        max_length=100,
        default="Phono Solar PS420M7GFH-18/VNH",
    )
    modulleistungWp = models.PositiveIntegerField(default=420)
    modulanzahl = models.IntegerField(
        default=0, validators=[MinValueValidator(-50)]
    )
    # Zubehör
    elwa = models.BooleanField(default=False)
    thor = models.BooleanField(default=False)
    heizstab = models.BooleanField(default=False)
    notstrom = models.BooleanField(default=False)
    optimizer = models.BooleanField(default=False)
    anzOptimizer = models.IntegerField(default=0)
    apzFeld = models.BooleanField(default=False)
    zaehlerschrank = models.BooleanField(default=False)
    potentialausgleich = models.BooleanField(default=False)
    beta_platte = models.BooleanField(default=False)
    metall_ziegel = models.BooleanField(default=False)
    prefa_befestigung = models.BooleanField(default=False)
    midZaehler = models.PositiveIntegerField(default=0)
    wallbox = models.BooleanField(default=False)
    wallboxtyp = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    wallbox_anzahl = models.PositiveIntegerField(default=0)
    geruestKunde = models.BooleanField(default=False)
    geruestOeffentlich = models.BooleanField(default=False)
    smartDongleLte = models.BooleanField(default=False)
    dachhakenKunde = models.BooleanField(default=False)

    # Result Prices :
    solar_module_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    batteriespeicher_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    smartmeter_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    wallbox_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    notstrom_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    optimizer_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )

    angebotsumme = models.FloatField(default=0.00, validators=[MinValueValidator(0)])

    # Files and other fields:
    profile_foto = models.BinaryField(blank=True, null=True)
    ticket_pdf = models.BinaryField(blank=True, null=True)
    ag_data = models.TextField(blank=True)
    ag_fetched_data = models.TextField(blank=True, null=True)
    countdown_on = models.BooleanField(default=False)

    def get_optional_accessory_price(self, name):
        return float(OptionalAccessoriesPreise.objects.get(name=name).price)

    def get_module_preis(self, name):
        return float(SolarModulePreise.objects.get(name=name).price)

    def get_module_garantie(self, name):
        try:
            out = str(SolarModulePreise.objects.get(name=name).module_garantie)
        except:
            out = ""
        return out

    def get_leistungs_garantie(self, name):
        try:
            out = str(SolarModulePreise.objects.get(name=name).leistungs_garantie)
        except:
            out = ""
        return out

    def get_wallbox_text(self, name):
        try:
            out = str(WallBoxPreise.objects.get(name=name).pdf_text)
        except:
            out = ""
        return out

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = self.generate_ticket_id()
            action_flag = ADDITION
        else:
            action_flag = CHANGE

        self.zoho_kundennumer = self.kundennumer_finder
        self.angenommenes_angebot = self.angebot_finder
        self.modulleistungWp = self.extract_modulleistungWp_from_name
        self.wallbox_angebot_price = self.full_wallbox_preis
        self.notstrom_angebot_price = self.get_optional_accessory_price("backup_box")
        self.optimizer_angebot_price = float(self.full_optimizer_preis)
        self.name = self.swap_name_order
        self.name_display_value = self.swap_name_order_PDF
        self.batteriespeicher_angebot_price = self.batteriespeicher_preis
        self.smartmeter_angebot_price = self.smartmeter_preis
        tmpSumme, tmpRabatt = self.angebots_summe
        self.angebotsumme = round(tmpSumme, 2)
        self.anfrage_vom = self.get_current_date_formatted
        self.ag_data = self.data
        super(VertriebTicket, self).save(*args, **kwargs)

        CustomLogEntry.objects.log_action(
            user_id=self.user_id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.pk,
            object_repr=str(self.ticket_id),
            action_flag=action_flag,
        )

    def __str__(self) -> str:
        return f"{self.ticket_id}"

    def generate_ticket_id(self):
        if self.user_id:
            user = User.objects.get(id=self.user.pk)
            kurz = user.kuerzel  # Assuming 'kuerzel' is an attribute of User
            current_datetime = datetime.datetime.now()
            return f"ZV-{kurz}{current_datetime.strftime('%d%m%Y-%H%M%S')}"
        else:
            # Return a default ID
            current_datetime = datetime.datetime.now()
            return f"ZV-DEFAULT{current_datetime.strftime('%d%m%Y-%H%M%S')}"

    def get_absolute_url(self):
        return reverse("edit_ticket_new", args=[str(self.angebot_id)])

    def delete(self, *args, **kwargs):
        # Log deletion before actually deleting
        CustomLogEntry.objects.log_action(
            user_id=self.user_id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.pk,
            object_repr=str(self),
            action_flag=DELETION,
        )
        super().delete(*args, **kwargs)

    @property
    def get_current_date_formatted(self):
        if self.anfrage_vom == None or self.anfrage_vom == "":
            current_datetime = datetime.datetime.now()
            self.anfrage_vom = current_datetime.strftime("%d-%b-%Y")
            return current_datetime.strftime("%d-%b-%Y")
        return self.anfrage_vom

    @property
    def firma_case(self):
        if self.anrede == "Firma":
            self.name_first_name = ""
            return self.name_last_name
        else:
            return self.name

    @property
    def assign_status_change_field(self):
        status_change_field = timezone.localtime(timezone.now())
        return status_change_field

    def countdown(self):
        if self.status_change_field:
            status_change_datetime = self.status_change_field

            delta = timezone.now() - status_change_datetime
            # get the difference in time

            # Check that status_change_field is within the past 14 days
            if delta.days < 0 or delta.days > 14:
                return None

            total_seconds = (
                14 * 24 * 60 * 60 - delta.total_seconds()
            )  # convert the difference to seconds

            # calculate days, hours, minutes
            days, remaining_seconds = divmod(total_seconds, 60 * 60 * 24)
            hours, remaining_seconds = divmod(remaining_seconds, 60 * 60)
            minutes = remaining_seconds // 60

            if total_seconds <= 0:
                return "0 days, 0 hours, 0 minutes"

            return f"{int(days)} Tage, {int(hours)} Stunde, {int(minutes)} Minute"
        else:
            return None

    @property
    def swap_name_order(self):
        if self.anrede == "Firma":
            parts = self.name_last_name
        elif self.anrede == "Familie":
            parts = self.name_last_name
        else:
            if self.name_suffix:
                parts = (
                    str(self.name_last_name)
                    + ", "
                    + str(self.name_suffix)
                    + " "
                    + str(self.name_first_name)
                )
            else:
                parts = str(self.name_last_name) + ", " + str(self.name_first_name)
        return str(parts)

    @property
    def swap_name_order_PDF(self):
        if self.anrede == "Firma":
            parts = self.name_last_name
        elif self.anrede == "Familie":
            parts = self.name_last_name
        else:
            if self.name_suffix:
                parts = (
                    str(self.name_suffix)
                    + " "
                    + str(self.name_first_name)
                    + " "
                    + str(self.name_last_name)
                )
            else:
                parts = str(self.name_first_name) + " " + str(self.name_last_name)
        return str(parts)

    @property
    def kundennumer_finder(self):
        if self.zoho_kundennumer:
            return self.zoho_kundennumer

        if not self.zoho_id:
            return ""

        try:
            data = json.loads(
                self.user.zoho_data_text
                or '[{"zoho_id": "default", "zoho_kundennumer": "default"}]'
            )
        except json.JSONDecodeError:
            return ""

        zoho_id = str(self.zoho_id)
        return next(
            (
                item["zoho_kundennumer"]
                for item in data
                if item.get("zoho_id") == zoho_id
            ),
            "",
        )

    @property
    def angebot_finder(self):
        angebote = VertriebAngebot.objects.filter(zoho_id=self.zoho_id)
        for an in angebote:
            if an.angebot_id == an.angenommenes_angebot:
                return an.angebot_id
        return ""

    @property
    def bauteile_finder(self):
        if VertriebAngebot.objects.filter(angebot_id=self.angenommenes_angebot):
            angebot = VertriebAngebot.objects.get(angebot_id=self.angenommenes_angebot)
            bauteileStr = ""
            if angebot.modulanzahl > 0:
                bauteileStr += str(angebot.modulanzahl) + "x " + angebot.solar_module + "\n"
            if angebot.anzOptimizer > 0:
                bauteileStr += str(angebot.anzOptimizer) + "x Optimierer" + "\n"
            if angebot.anz_speicher > 0:
                bauteileStr += str(angebot.anz_speicher) + "x Batteriemodul " + angebot.speicher_model + "\n"
            if angebot.wallbox_anzahl > 0:
                bauteileStr += str(angebot.wallbox_anzahl) + "x  " + angebot.wallboxtyp + "\n"
            return bauteileStr
        return ""

    @property
    def get_building_insights(
        self, latitude=None, longitude=None, requiredQuality="HIGH"
    ):
        # Replace with your Solar API key if different
        if self.postanschrift_latitude and self.postanschrift_longitude:
            latitude = float(self.postanschrift_latitude)
            longitude = float(self.postanschrift_longitude)
        else:
            latitude, longitude = self.coordinates_extractor
        url = f"https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude={latitude}&location.longitude={longitude}&requiredQuality={requiredQuality}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        return response.json()

    @property
    def google_maps_url(self):
        if self.postanschrift_latitude and self.postanschrift_longitude:
            latitude = float(self.postanschrift_latitude)
            longitude = float(self.postanschrift_longitude)
            maps_url = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=14/{latitude}/{longitude}"
            return maps_url
        elif not self.postanschrift_latitude or not self.postanschrift_longitude:
            latitude, longitude = self.coordinates_extractor
            maps_url = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=14/{latitude}/{longitude}"
            return maps_url
        else:
            return ""

    @property
    def get_vertribler(self):
        return f"{self.user.first_name} {self.user.last_name} \nMobil: {self.user.phone}\nEmail: {self.user.email}"  # type: ignore

    @property
    def vertrieb_abk(self):
        return f"{self.user.kuerzel}"  # type: ignore

    @property
    def angebot_gultig(self):
        current_date = datetime.datetime.now()
        frist = current_date + timedelta(days=14)
        return frist.strftime("%d.%m.%Y")

    """

    CALCULATING   KUNDEN DATAS  

    """

    @property
    def full_adresse(self):
        return f"{self.strasse}\n{self.ort}"

    @property
    def anlagen_standort(self):
        if self.anlagenstandort:
            return self.anlagenstandort
        else:
            return f"{self.strasse}, {self.ort}"

    @property
    def extract_modulleistungWp_from_name(self):
        match = re.search(r"(\d+)", str(self.solar_module))
        if match:
            return int(match.group(1))
        return 420


    @property
    def leistungsmodul_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="leistungsmodul").price)

    @property
    def stromgrundpreis_gesamt(self):
        return round(float(self.grundpreis) * 12 * int(self.zeitraum), 2)

    @staticmethod
    def priceInflation(pricePerYear, increasePerYear, years):
        sumPrice = 0
        priceList = []
        for i in range(years):
            sumPrice += pricePerYear
            priceList.append(sumPrice)
            pricePerYear = pricePerYear * (1.0 + increasePerYear)
        return sumPrice, priceList

    """

    CALCULATING   SOLAR MODULE PARAMETERS  

    """

    @staticmethod
    def get_values():
        return {obj.name: obj.zuschlag for obj in SolarModulePreise.objects.all()}

    @staticmethod
    def get_prices():
        return {obj.name: obj.price for obj in OptionalAccessoriesPreise.objects.all()}

    @staticmethod
    def get_module_prices():
        return {obj.name: obj.price for obj in SolarModulePreise.objects.all()}

    def calculate_price(self, model, name, multiplier):
        try:
            multiplier = int(multiplier)
        except ValueError:
            multiplier = 0
        price = get_price(model, name)
        return price * multiplier

    @property
    def modulleistung_price(self):
        prices = self.get_prices()
        return float(prices[ACCESSORY_NAME])

    @property
    def elwa_price(self):
        prices = self.get_prices()
        return float(prices["elwa_2"])

    @property
    def thor_price(self):
        prices = self.get_prices()
        return float(prices["ac_thor_3_kw"])

    @property
    def heizstab_price(self):
        prices = self.get_prices()
        return float(prices["heizstab"])

    @property
    def solar_module_gesamt_preis(self):
        module_prices = self.get_module_prices()
        module_name = (
            self.solar_module if self.solar_module else "Phono Solar PS420M7GFH-18/VNH"
        )
        try:
            return float(module_prices[module_name]) * int(self.modulanzahl)
        except KeyError:
            # handle the error, maybe return a default value or raise a more descriptive error
            return 0.0

    @property
    def beta_platte_preis(self):
        limits = [7, 11, 15, 19, 23, 27, 30]
        kwp = min(30, self.modulsumme_kWp)
        kwpUpper = min(upper for upper in limits if upper >= kwp)
        namePlatte = "BetaPlatte" + str(kwpUpper)
        beta_preis = float(KwpPreise.objects.get(name=namePlatte).price)
        return beta_preis

    @property
    def metall_ziegel_preis(self):
        limits = [7, 11, 15, 19, 23, 27, 30]
        kwp = min(30, self.modulsumme_kWp)
        kwpUpper = min(upper for upper in limits if upper >= kwp)
        nameZiegel = "MetallZiegel" + str(kwpUpper)
        ziegel_preis = float(KwpPreise.objects.get(name=nameZiegel).price)
        return ziegel_preis

    @property
    def prefa_befestigung_preis(self):
        prefa_preis = OptionalAccessoriesPreise.objects.get(name="prefa_befestigung").price * self.modulanzahl
        return prefa_preis
    @property
    def wandhalterung_fuer_speicher_preis(self):
        wandhalterung_preis = 0
        if self.anz_wandhalterung_fuer_speicher != 0:
            anz_wandhalterung_fuer_speicher = int(self.anz_wandhalterung_fuer_speicher)
            wandhalterung_preis = self.calculate_price(
                OptionalAccessoriesPreise,
                "wandhalterung_fuer_speicher",
                anz_wandhalterung_fuer_speicher,
            )

            return wandhalterung_preis

    @property
    def midZaehler_preis(self):
        midZaehler_preis = 0
        if self.midZaehler != 0:
            anz_midZaehler = int(self.midZaehler)
            midZaehler_preis = self.calculate_price(
                OptionalAccessoriesPreise,
                "mid_zaehler",
                anz_midZaehler,
            )
            return midZaehler_preis

    @property
    def batteriespeicher_preis(self):
        batterieDict = {"LUNA 2000-5-S0": "batteriemodul_huawei5", "LUNA 2000-7-S1": "batteriemodul_huawei7",
                        "Vitocharge VX3 PV-Stromspeicher": "batteriemodul_viessmann"}
        leistModDict = {"LUNA 2000-5-S0": True, "LUNA 2000-7-S1": True, "Vitocharge VX3 PV-Stromspeicher": False}
        batteriePreis = 0
        if self.anz_speicher != 0:
            anz_speicher = int(self.anz_speicher)
            leistungsmodulNotwendig = leistModDict.get(self.speicher_model)
            batterieDatensatz = batterieDict.get(self.speicher_model)
            # Kein angenommenes Angebot oder angenommenes Angebot hatte keinen Speicher
            if batterieDatensatz is not None and (not VertriebAngebot.objects.filter(angebot_id=self.angenommenes_angebot)
                or VertriebAngebot.objects.get(angebot_id=self.angenommenes_angebot).anz_speicher == 0):
                batteriePreis = self.calculate_price(OptionalAccessoriesPreise, batterieDatensatz, anz_speicher)
                if leistungsmodulNotwendig:
                    batteriePreis = float(batteriePreis) + ceil(anz_speicher / 3) * float(self.leistungsmodul_preis)
                # Falls mehr als 6 Speichermodule bei Huawei 7 eventuell Zusatzwechselrichter notwendig wegen fehlenden Steckplätzen
                if self.modulsumme_kWp < 25.0 and self.speicher_model == "LUNA 2000-7-S1" and anz_speicher > 6:
                    batteriePreis += self.get_optional_accessory_price("zusatzwechselrichter")
                return batteriePreis
            # Angenommenes Angebot mit angebotenem Speicher
            elif VertriebAngebot.objects.filter(angebot_id=self.angenommenes_angebot):
                angebot = VertriebAngebot.objects.get(angebot_id=self.angenommenes_angebot)
                # gleiches Speichermodell
                if self.speicher_model == angebot.speicher_model:
                    batteriePreis = self.calculate_price(OptionalAccessoriesPreise, batterieDatensatz, anz_speicher)
                    if leistungsmodulNotwendig:
                        batteriePreis = float(batteriePreis) + ceil((anz_speicher + angebot.anz_speicher) / 3) * float(self.leistungsmodul_preis)
                        batteriePreis = float(batteriePreis) - ceil(angebot.anz_speicher / 3) * float(self.leistungsmodul_preis)
                # abweichendes Speichermodell
                else:
                    batteriePreis = self.calculate_price(OptionalAccessoriesPreise, batterieDatensatz, anz_speicher)
                    batteriePreis -= self.calculate_price(OptionalAccessoriesPreise, batterieDict.get(angebot.speicher_model), angebot.anz_speicher)
                    if leistungsmodulNotwendig:
                        batteriePreis = float(batteriePreis) + ceil(anz_speicher / 3) * float(self.leistungsmodul_preis)
                        batteriePreis = float(batteriePreis) - ceil(angebot.anz_speicher / 3) * float(self.leistungsmodul_preis)
                # Falls mehr als 6 Speichermodule bei Huawei 7 eventuell Zusatzwechselrichter notwendig wegen fehlenden Steckplätzen, falls Limit jetzt erst überschritten
                if self.modulsumme_kWp < 25.0 and self.speicher_model == "LUNA 2000-7-S1" and angebot.anz_speicher <= 6 and (anz_speicher + angebot.anz_speicher) > 6:
                    batteriePreis += self.get_optional_accessory_price("zusatzwechselrichter")
        return batteriePreis

    @property
    def smartmeter_preis(self):
        smartmeterPreis = 0
        if self.smartmeter_model == "Smart Power Sensor DTSU666H":
            smartmeterPreis = self.calculate_price(
                    OptionalAccessoriesPreise, "smartmeter_dtsu", 1
                )
        elif self.smartmeter_model == "EMMA-A02":
            smartmeterPreis = self.calculate_price(
                OptionalAccessoriesPreise, "smartmeter_emma", 1
            )
        elif self.smartmeter_model == "Viessmann Energiezähler":
            smartmeterPreis = self.calculate_price(
                OptionalAccessoriesPreise, "smartmeter_viessmann", 1
            )
        return smartmeterPreis

    @property
    def modulsumme_kWp(self):
        return round(self.existing_kWp + self.ticket_kwp,2)

    @property
    def existing_kWp(self):
        existing = 0
        if self.angenommenes_angebot != "" and VertriebAngebot.objects.filter(angebot_id=self.angenommenes_angebot):
            existing = VertriebAngebot.objects.get(angebot_id=self.angenommenes_angebot).modulsumme_kWp
        return round(existing, 2)

    @property
    def ticket_kwp(self):
        return round(self.modulleistungWp * self.modulanzahl / 1000, 2)

    @property
    def anz_leistungs_module(self):
        if self.angenommenes_angebot != "" and VertriebAngebot.objects.filter(angebot_id=self.angenommenes_angebot):
            angebot = VertriebAngebot.objects.get(angebot_id=self.angenommenes_angebot)
            return ceil((self.anz_speicher + angebot.anz_speicher)/ 3) - ceil(angebot.anz_speicher / 3)
        else:
            return ceil(self.anz_speicher / 3)

    @property
    def get_zuschlag(self):
        # Fetch all the values
        values = self.get_values()

        # Check if 'self.solar_module' is not None, else assign the default module name
        module_name = (self.solar_module if self.solar_module else ("Phono Solar PS420M7GFH-18/VNH"))
        # Return value based on module_name
        return float(values.get(module_name))

    """

    CALCULATING   WALLBOX  

    """

    @property
    def wallbox_anzahl_pdf(self):
        if self.wallbox_anzahl and self.wallbox_anzahl > 3:
            raise ValueError(
                "Achtung, mehr als 3 Wallboxen ausgewählt, bitte Preise für Harvi & Hub bzw. Power Boost überprüfen."
            )
        return (
            "\n1\n1"
            if "Zappi" in str(self.wallboxtyp)
            else "\n1" if "Power Boost" in str(self.wallboxtyp) else "\n1"
        )

    @property
    def wallbox_kabel_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="kabelpreis").price)

    @property
    def optimizer_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="optimizer").price)

    @property
    def optimizer_full_preis(self):
        return self.anzOptimizer * self.optimizer_preis

    """

    CALCULATING   ANGEBOT SUMME  

    """

    @property
    def full_optimizer_preis(self):
        return self.anzOptimizer * self.get_optional_accessory_price("optimizer")

    @property
    def full_wallbox_preis(self):
        if self.wallbox_anzahl:
            preis = float(WallBoxPreise.objects.get(name=str(self.wallboxtyp)).price)
            preis *= self.wallbox_anzahl
            return preis
        else:
            return 0.00

    @property
    def full_accessories_price(self):
        accessories_price = 0
        if self.full_optimizer_preis:
            accessories_price += float(self.full_optimizer_preis)
        if self.full_wallbox_preis:
            accessories_price += float(self.full_wallbox_preis)
        if self.batteriespeicher_angebot_price:
            accessories_price += float(self.batteriespeicher_angebot_price)
        if self.smartmeter_angebot_price:
            accessories_price += float(self.smartmeter_angebot_price)
        if self.notstrom:
            accessories_price += float(self.get_optional_accessory_price("backup_box"))
        if self.smartDongleLte:
            accessories_price += float(self.get_optional_accessory_price("smartDongleLte"))
        if self.midZaehler > 0:
            accessories_price += float(self.midZaehler_preis)
        if self.apzFeld:
            accessories_price += float(self.get_optional_accessory_price("apzFeld"))
        if self.zaehlerschrank:
            accessories_price += float(self.get_optional_accessory_price("zaehlerschrank"))
        if self.potentialausgleich:
            accessories_price += float(self.get_optional_accessory_price("potentialausgleich"))
        if self.beta_platte:
            accessories_price += float(self.beta_platte_preis)
        if self.metall_ziegel:
            accessories_price += float(self.metall_ziegel_preis)
        if self.prefa_befestigung:
            accessories_price += float(self.prefa_befestigung_preis)
        if self.wandhalterung_fuer_speicher_preis:
            accessories_price += float(self.wandhalterung_fuer_speicher_preis)
        if self.elwa:
            accessories_price += float(self.elwa_price)
        if self.thor:
            accessories_price += float(self.thor_price)
        if self.heizstab:
            accessories_price += float(self.heizstab_price)
        return accessories_price

    @property
    def angebots_summe(self):
        angebotsSumme = float(SolarModulePreise.objects.get(name=self.solar_module).price * self.modulanzahl)
        angebotsSumme += float(self.full_accessories_price)

        rabatt = 0

        userAufschlag = float(self.user.users_aufschlag) / 100 + 1  # type: ignore
        angebotsSumme *= userAufschlag
        # Abzug Selbstleistungen nach Rabattierung
        if self.geruestKunde:
            angebotsSumme -= float(self.get_optional_accessory_price("geruestKunde"))
            rabatt += float(self.get_optional_accessory_price("geruestKunde"))
        elif self.geruestOeffentlich:
            angebotsSumme += float(self.get_optional_accessory_price("geruestOeffentlich"))
        if self.dachhakenKunde:
            angebotsSumme -= float(self.get_optional_accessory_price("dachhakenKunde"))
            rabatt += float(self.get_optional_accessory_price("dachhakenKunde"))
        return angebotsSumme, rabatt


    @property
    def kosten_pva(self):
        return float(self.angebots_summe[0]) * float(
            1 + AndereKonfigurationWerte.objects.get(name="steuersatz").value
        )

    @property
    def data(self):
        dt = {
            "firma": self.firma,
            "anrede": self.anrede,
            "kunde": self.name_display_value,
            "adresse": self.full_adresse,
            "vertriebler": str(self.get_vertribler),
            "vertriebAbk": self.vertrieb_abk,
            "gueltig": self.angebot_gultig,
            "module": self.solar_module,
            "wpModule": self.modulleistungWp,
            "anzModule": self.modulanzahl,
            "produktGarantie": self.get_module_garantie(self.solar_module),
            "leistungsGarantie": self.get_leistungs_garantie(self.solar_module),
            "kWp": round(self.modulsumme_kWp,2),
            "kWpOhneRundung": self.modulsumme_kWp,
            "existing_kWp":self.existing_kWp,
            "ticket_kWp":self.ticket_kwp,
            "standort": self.anlagen_standort,
            "batterieVorh": self.batteriespeicher_preis,
            "batterieModell": self.speicher_model,
            "smartmeterModell": self.smartmeter_model,
            "wandhalterungSpeicher": self.wandhalterung_fuer_speicher,
            "anzWandhalterungSpeicher": self.anz_wandhalterung_fuer_speicher,
            "wandhalterungSpeicherPreis": self.wandhalterung_fuer_speicher_preis,
            "batterieAnz": self.anz_speicher,
            "leistModAnz": self.anz_leistungs_module,
            "wallboxVorh": self.full_wallbox_preis,
            "wallboxTyp": self.wallboxtyp,
            "wallboxText": self.get_wallbox_text(self.wallboxtyp),
            "wallboxAnz": self.wallbox_anzahl,
            "optionVorh": self.notstrom,
            "elwa": self.elwa,
            "thor": self.thor,
            "midZaehler": self.midZaehler,
            "apzFeld": self.apzFeld,
            "zaehlerschrank": self.zaehlerschrank,
            "potentialausgleich": self.potentialausgleich,
            "geruestKunde": self.geruestKunde,
            "geruestOeffentlich": self.geruestOeffentlich,
            "dachhakenKunde": self.dachhakenKunde,
            "betaPlatte": self.beta_platte,
            "metallZiegel": self.metall_ziegel,
            "prefaBefestigung": self.prefa_befestigung,
            "heizstab": self.heizstab,
            "smartDongleLte": self.smartDongleLte,
            "optimierer": self.optimizer,
            "anzOptimierer": self.anzOptimizer,
            "notstrom": self.notstrom,
            "solarModulePreis": self.solar_module_gesamt_preis,
            "wallboxPreis": self.full_wallbox_preis,
            "notstromPreis": self.get_optional_accessory_price("backup_box"),
            "batterieSpeicherPreis": self.batteriespeicher_preis,
            "gesamtOptimizerPreis": self.full_optimizer_preis,
            "angebotssumme": self.angebotsumme,
            "steuersatz": float(
                AndereKonfigurationWerte.objects.get(name="steuersatz").value
            ),
            "kostenPVA": self.kosten_pva,
            "debug": False,
            "version": 1.0,
        }
        return dt



class Editierbarer_Text(models.Model):
    """
    Modell, das einen bearbeitbaren Textblock in einem PDF-Dokument darstellt.
    """

    identifier = models.CharField(max_length=255, unique=True)
    content = models.TextField(help_text="Inhalt", default="<<kein editierbarer text>>")
    font = models.CharField(
        help_text="Schrift", max_length=100, default="JUNO Solar Lt"
    )
    font_size = models.IntegerField(help_text="Schriftgröße", default=11)
    x = models.FloatField(help_text="x-Koordinate", default=0.00)
    y = models.FloatField(help_text="y-Koordinate", default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return f"{self.identifier}   -   X={self.x}; Y={self.y}; Schriftgröße: {self.font_size}pt;"
    def __str__(self):
        return f"""
Editierbarer_Text.objects.create(
    identifier="{self.identifier}", 
    content="{self.content}", 
    font="{self.font}", 
    x={self.x},
    y={self.y},
    font_size={self.font_size}
)"""


class Dokument_PDF(models.Model):
    """
    Modell, das ein PDF-Dokument darstellt, das mehrere bearbeitbare Texte enthalten kann.
    """

    title = models.CharField(max_length=255, default="Dokument PDF Vertrieb")
    editable_texts = models.ManyToManyField(Editierbarer_Text)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
