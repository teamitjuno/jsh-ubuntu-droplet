from os import path
from django.db import models
import hashlib
from authentication.models import User
from shared.models import TimeStampMixin
from django.core.validators import MinValueValidator
from prices.models import (
    ModuleGarantiePreise,
    ModulePreise,
    OptionalAccessoriesPreise,
    AndereKonfigurationWerte,
    SolarModulePreise,
    WallBoxPreise,
)
from django.contrib.auth import get_user_model
import datetime, os
from datetime import timedelta
from math import ceil
import re, json, requests
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils.formats import date_format
import dateparser
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

now = timezone.now()
now_german = date_format(now, "DATETIME_FORMAT")
User = get_user_model()


def extract_modulleistungWp(model_name):
    # Split the name by spaces and filter out parts that are purely digits
    parts = model_name.split()
    for part in parts:
        if part.isdigit():
            return int(part)
    return None


def get_modulleistungWp_from_map(module_name_map):
    result = {}
    for model_name, description in module_name_map.items():
        power = extract_modulleistungWp(description)
        if power:
            result[model_name] = power
    return result


class LogEntryManager(models.Manager):
    def log_action(
        self, user_id, content_type_id, object_id, object_repr, action_flag, status=None
    ):
        change_message = ""  # default value

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

    objects = LogEntryManager()  # don't forget to set the manager

    def get_vertrieb_angebot(self):
        from vertrieb_interface.models import VertriebAngebot

        if self.content_type.model_class() == VertriebAngebot:
            try:
                return VertriebAngebot.objects.get(angebot_id=self.object_id)
            except VertriebAngebot.DoesNotExist:
                # Handle the case where no matching record is found
                # For instance, return None, or handle it in another appropriate way for your application
                return VertriebAngebot.objects.filter(angebot_id=self.object_id).first()
        return None

    def get_change_message(self):
        if self.is_addition():
            return f"Ein neues Angebot erstellt"
        elif self.is_change():
            if self.get_vertrieb_angebot() is not None:
                return f"Der Angebot aktualisiert -  {self.change_message}"
            else:
                return f"Der Angebot aktualisiert"
        elif self.is_deletion():
            return f"Der Angebot aktualisiert"
        else:
            return "LogEntry Object"


def sanitize_cache_key(key):
    sanitized_key = hashlib.md5(key.encode()).hexdigest()
    return sanitized_key


def get_price(model, name):
    model_name = model.__name__
    key = f"{model_name}_{name}"

    # Sanitize the key before using it with cache
    sanitized_key = sanitize_cache_key(key)

    price = cache.get(sanitized_key)
    if price is None:
        try:
            price = model.objects.get(name=name).price
        except ObjectDoesNotExist:
            price = 0
        cache.set(sanitized_key, price)
    return price


# Model properties
MODULE_NAME_MAP = {
    "Phono Solar PS420M7GFH-18/VNH": "Phono Solar PS420M7GFH-18/VNH",
    "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B": "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B",
}
ACCESSORY_NAME = "leistungsmodul"
BATT_DICT = {1: 0.6, 2: 0.7, 3: 0.75, 4: 0.8, 5: 0.85, 6: 0.92}
DEFAULT_BATT_USAGE = 0.3
ANGEBOT_STATUS_CHOICES = [
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


class VertriebAngebot(TimeStampMixin):
    angebot_id = models.CharField(max_length=255, unique=True, primary_key=True)
    current_date = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_locked = models.BooleanField(default=False)

    #   ZOHO FIELDS
    zoho_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        choices=ANGEBOT_STATUS_CHOICES,
        default="in Kontakt",
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
    ANREDE_CHOICES = (
        ("Familie", "Familie"),
        ("Firma", "Firma"),
        ("Herr", "Herr"),
        ("Herr Dr.", "Herr Dr."),
        ("Herr Prof.", "Herr Prof."),
        ("Frau", "Frau"),
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

    anrede = models.CharField(choices=ANREDE_CHOICES, blank=True, max_length=20)
    name = models.CharField(max_length=100, blank=True)
    vorname_nachname = models.CharField(max_length=100, blank=True, null=True)
    firma = models.CharField(max_length=100, blank=True)
    strasse = models.CharField(max_length=100, blank=True)
    ort = models.CharField(max_length=100, blank=True)
    anlagenstandort = models.CharField(max_length=100, blank=True, null=True)
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
    speicher = models.BooleanField(default=False)
    anz_speicher = models.PositiveIntegerField(default=0)
    wandhalterung_fuer_speicher = models.BooleanField(default=False)
    anz_wandhalterung_fuer_speicher = models.PositiveIntegerField(default=0)
    wallbox = models.BooleanField(default=False)
    ausrichtung = models.CharField(
        max_length=10, choices=AUSRICHTUNG_CHOICES, default="Ost/West"
    )
    komplex = models.CharField(
        max_length=30, choices=KOMPLEX_CHOICES, default="sehr komplex"
    )
    GARANTIE_WR_CHOICES = [
        ("keine", "keine"),
        ("10 Jahre", "10 Jahre"),
        ("15 Jahre", "15 Jahre"),
        ("20 Jahre", "20 Jahre"),
    ]
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
    eddi = models.BooleanField(default=False)
    elwa = models.BooleanField(default=False)
    elwa_typ = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    thor = models.BooleanField(default=False)
    thor_typ = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    notstrom = models.BooleanField(default=False)
    optimizer = models.BooleanField(default=False)
    anzOptimizer = models.PositiveIntegerField(default=0)

    wallboxtyp = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    wallbox_anzahl = models.PositiveIntegerField(default=0)
    kabelanschluss = models.FloatField(
        default=10.0, validators=[MinValueValidator(0)], blank=True, null=True
    )
    hub_included = models.BooleanField(default=False)

    module_ticket = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    modul_anzahl_ticket = models.IntegerField(default=0)
    optimizer_ticket = models.IntegerField(default=0)
    batteriemodule_ticket = models.IntegerField(default=0)
    notstrom_ticket = models.IntegerField(default=0)
    eddi_ticket = models.IntegerField(default=0)
    indiv_price_included = models.BooleanField(default=False)
    indiv_price = models.FloatField(default=0.00, validators=[MinValueValidator(0)])
    angebot_id_assigned = models.BooleanField(default=False)

    total_anzahl = models.IntegerField(blank=True, null=True)

    solar_module_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    batteriespeicher_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    wallbox_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    notstrom_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    eddi_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    optimizer_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    angebotsumme = models.FloatField(default=0.00, validators=[MinValueValidator(0)])
    fullticketpreis = models.FloatField(default=0.00, validators=[MinValueValidator(0)])

    profile_foto = models.BinaryField(blank=True, null=True)
    angebot_pdf = models.BinaryField(blank=True, null=True)
    angebot_pdf_admin = models.BinaryField(blank=True, null=True)
    calc_pdf = models.BinaryField(blank=True, null=True)
    calc_graph_img = models.ImageField(null=True, blank=True)
    ticket_pdf = models.BinaryField(blank=True, null=True)
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
    ag_data = models.TextField(blank=True)
    Rest_liste = models.TextField(blank=True, null=True)
    Arbeits_liste = models.TextField(blank=True, null=True)
    Full_ticket_preis = models.FloatField(default=0.00)
    countdown_on = models.BooleanField(default=False)

    def get_optional_accessory_price(self, name):
        return float(OptionalAccessoriesPreise.objects.get(name=name).price)

    def get_module_preis(self, name):
        return float(SolarModulePreise.objects.get(name=name).price)

    def get_module_garantie_preis(self, name):
        return float(ModuleGarantiePreise.objects.get(name=name).price)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.angebot_id = self.generate_angebot_id()
            action_flag = ADDITION
        else:
            action_flag = CHANGE

        (
            self.postanschrift_latitude,
            self.postanschrift_longitude,
        ) = self.coordinates_extractor
        self.modulleistungWp = self.extract_modulleistungWp_from_name
        self.wallbox_angebot_price = self.full_wallbox_preis
        self.notstrom_angebot_price = self.get_optional_accessory_price("backup_box")
        self.optimizer_angebot_price = float(self.full_optimizer_preis)
        self.eddi_angebot_price = float(self.get_optional_accessory_price("eddi"))
        if self.batteriespeicher_preis:
            self.batteriespeicher_angebot_price = self.batteriespeicher_preis
        self.angebotsumme = round(self.angebots_summe, 2)
        self.fullticketpreis = self.full_ticket_preis
        self.benotigte_restenergie = self.restenergie
        self.nutzbare_nutzenergie = self.nutz_energie
        self.erzeugte_energie_pro_jahr = self.erzeugte_energie
        self.einspreisevergütung_gesamt = self.einsp_verg
        self.abzug_vergutung = self.abzug
        self.Ersparnis = self.ersparnis
        self.kosten_fur_restenergie = self.kosten_rest_energie
        self.ag_data = self.data
        self.total_anzahl = self.Total_anzahl
        self.Rest_liste = self.rest_liste
        self.Arbeits_liste = self.arbeits_liste
        self.Full_ticket_preis = self.full_ticket_preis

        super().save(*args, **kwargs)

        CustomLogEntry.objects.log_action(
            user_id=self.user_id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.pk,
            object_repr=str(self),
            action_flag=action_flag,
        )

    def __str__(self) -> str:
        return f"AngebotID: {self.angebot_id}"

    def generate_angebot_id(self):
        user = User.objects.get(id=self.user.pk)
        kurz = user.kuerzel  # type: ignore
        current_datetime = datetime.datetime.now()
        return f"AN-{kurz}{current_datetime.strftime('%d%m%Y-%H%M%S')}"

    def get_absolute_url(self):
        return reverse("edit_angebot", args=[str(self.angebot_id)])

    def delete(self, *args, **kwargs):
        # Log deletion before actually deleting
        CustomLogEntry.objects.log_action(
            user_id=self.user_id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.pk,
            object_repr=str(self),
            action_flag=DELETION,  # Assuming DELETION is a flag you have defined somewhere
        )
        super().delete(*args, **kwargs)

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

    # @property
    # def mapbox_data(self):
    #     MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
    #     OWNER_ID = os.getenv('OWNER_ID')
    #     STYLE_ID = os.getenv('STYLE_ID')

    #     data = {
    #         "token": MAPBOX_TOKEN,
    #
    #         "latitude": None,
    #         "longitude": None
    #     }

    #     if self.postanschrift_latitude and self.postanschrift_longitude:
    #         data["latitude"] = float(self.postanschrift_latitude)
    #         data["longitude"] = float(self.postanschrift_longitude)
    # url = <iframe width='100%' height='400px' src="https://api.mapbox.com/styles/v1/sam1206morfey/clldpoqf200zc01ph5h660576.html?title=false&access_token=pk.eyJ1Ijoic2FtMTIwNm1vcmZleSIsImEiOiJjbGtodXY3Z3cwZXk0M2VueW9jcWo0bmRlIn0.KDrGkX79RQxHcodui5opmA&zoomwheel=false#11/48.138/11.575" title="Navigation" style="border:none;"></iframe>
    #     return url

    @property
    def coordinates_extractor(self):
        # Return "0.0", "0.0" if strasse or ort is None
        if self.strasse is None or self.ort is None:
            return "0.0", "0.0"

        # Load variables from .env
        OWNER_ID = os.getenv("OWNER_ID")
        STYLE_ID = os.getenv("STYLE_ID")
        MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

        # Prepare the query string
        query = f"{self.strasse}, {self.ort}"

        # You might need to adjust this URL to match the Mapbox API version/documentation you're using
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json?access_token={MAPBOX_TOKEN}"

        # Make the API call
        response = requests.get(url)
        data = response.json()

        # Extracting latitude and longitude from the response
        try:
            longitude, latitude = data["features"][0]["geometry"]["coordinates"]
            return latitude, longitude
        except (IndexError, KeyError):
            # Handle cases where the address isn't found or the API response structure has unexpected changes
            return 0.0, 0.0

    @property
    def mapbox_data(self):
        MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
        OWNER_ID = os.getenv("OWNER_ID")
        STYLE_ID = os.getenv("STYLE_ID")

        data = {"token": MAPBOX_TOKEN, "latitude": None, "longitude": None}

        if self.postanschrift_latitude and self.postanschrift_longitude:
            data["latitude"] = float(self.postanschrift_latitude)
            data["longitude"] = float(self.postanschrift_longitude)

        url_template = "https://api.mapbox.com/styles/v1/{owner}/{style}.html?title=false&access_token={token}&zoomwheel=false#11/{lat}/{lon}"
        url = url_template.format(
            owner=OWNER_ID,
            style=STYLE_ID,
            token=MAPBOX_TOKEN,
            lat=data["latitude"] if data["latitude"] is not None else "48.138",
            lon=data["longitude"] if data["longitude"] is not None else "11.575",
        )

        return url

    @property
    def google_maps_url(self):
        if self.postanschrift_latitude and self.postanschrift_longitude:
            latitude = float(self.postanschrift_latitude)
            longitude = float(self.postanschrift_longitude)

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
            return OptionalAccessoriesPreise.objects.get(
                name=direction_map[direction]
            ).price
        else:
            return 0.00

    @property
    def get_leistungsgarantie(self):
        if "Phono Solar" in str(self.solar_module):
            return "30 Jahre"
        elif "Jinko Solar" in str(self.solar_module):
            return f"0,4 % Jährliche Degradation\n                                     über 30 Jahre"
        else:
            return "0,4 % Jährliche Degradation\n                                     über 30 Jahre"

    @property
    def get_produktgarantie(self):
        if "Phono Solar" in str(self.solar_module):
            return "15 Jahre"
        elif "Jinko Solar" in str(self.solar_module):
            return f"25 Jahre"
        else:
            return "15 Jahre"

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
        return {obj.name: obj.value for obj in AndereKonfigurationWerte.objects.all()}

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
    def Total_anzahl(self):
        total = 0
        if self.modulanzahl and self.modul_anzahl_ticket:
            total += self.modulanzahl + self.modul_anzahl_ticket
            return total
        else:
            return self.modulanzahl

    @property
    def modulleistung_price(self):
        prices = self.get_prices()
        return float(prices[ACCESSORY_NAME])

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
    def wandhalterung_fuer_speicher_preis(self):
        wandhalterung_preis = 0
        if (
            self.wandhalterung_fuer_speicher == True
            and self.anz_wandhalterung_fuer_speicher != 0
        ):
            anz_wandhalterung_fuer_speicher = int(self.anz_wandhalterung_fuer_speicher)
            wandhalterung_preis = self.calculate_price(
                OptionalAccessoriesPreise,
                "wandhalterung_fuer_speicher",
                anz_wandhalterung_fuer_speicher,
            )

            return wandhalterung_preis

    @property
    def batteriespeicher_preis(self):
        batteriePreis = 0
        if self.speicher == True and self.anz_speicher != 0:
            leistungsmodulePreis = self.leistungsmodul_preis
            anz_speicher = int(self.anz_speicher)
            batteriePreis = self.calculate_price(
                OptionalAccessoriesPreise, "batteriemodul", anz_speicher
            )
            batteriePreis = float(batteriePreis) + ceil(anz_speicher / 3) * float(
                leistungsmodulePreis
            )
            return batteriePreis

    @property
    def modulsumme_kWp(self):
        return self.modulleistungWp * self.modulanzahl / 1000

    @property
    def modulsumme(self):
        values = self.get_values()
        module_name = (
            self.solar_module if self.solar_module else "Phono Solar PS420M7GFH-18/VNH"
        )
        if module_name and (value := values.get(module_name + "_leistung")):
            return int(value * int(self.modulanzahl)) / 1000
        else:
            return 0

    @property
    def get_zuschlag(self):
        values = self.get_values()
        module_name = (
            self.solar_module.lower()
            if self.solar_module
            else ("Phono Solar PS420M7GFH-18/VNH").lower()
        )

        return values.get(
            module_name, "Phono Solar PS420M7GFH-18/VNH"
        )  # Add default value

    @property
    def nutz_energie(self):
        nutzEnergie = float(self.verbrauch)
        if self.erzeugte_energie < nutzEnergie:
            nutzEnergie = float(self.erzProJahr) * float(self.modulsumme_kWp)
        if self.speicher and self.anz_speicher != 0:
            nutzEnergie = nutzEnergie * BATT_DICT[self.anz_speicher]
        else:
            nutzEnergie = nutzEnergie * DEFAULT_BATT_USAGE
        return round(nutzEnergie, 2)

    @property
    def restenergie(self):
        return float(self.verbrauch) - float(self.nutz_energie)

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
    def wallbox_text(self):
        text = (
            "\nHarvi\nHub"
            if "Zappi" in str(self.wallboxtyp)
            else "Inkl. Power Boost"
            if "Power Boost" in str(self.wallboxtyp)
            else ""
        )
        return text

    @property
    def wallbox_anzahl_pdf(self):
        if self.wallbox_anzahl and self.wallbox_anzahl > 3:
            raise ValueError(
                "Achtung, mehr als 3 Wallboxen ausgewählt, bitte Preise für Harvi & Hub bzw. Power Boost überprüfen."
            )
        return (
            "\n1\n1"
            if "Zappi" in str(self.wallboxtyp)
            else "\n1"
            if "Power Boost" in str(self.wallboxtyp)
            else "\n1"
        )

    @property
    def wallbox_kabel_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="kabelpreis").price)

    @property
    def harvi_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="harvi").price)

    @property
    def optimizer_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="optimizer").price)

    @property
    def optimizer_full_preis(self):
        return self.anzOptimizer * self.optimizer_preis

    """

    CALCULATING   TICKET  

    """

    @property
    def modul_ticket_preis(self):
        name = self.module_ticket
        return self.calculate_price(
            SolarModulePreise, name, int(self.modul_anzahl_ticket)
        )

    @property
    def optimizer_ticket_preis(self):
        return self.calculate_price(
            OptionalAccessoriesPreise, "optimizer", int(self.optimizer_ticket)
        )

    @property
    def batterie_ticket_preis(self):
        return self.calculate_price(
            OptionalAccessoriesPreise, "batteriemodul", int(self.batteriemodule_ticket)
        )

    @property
    def leistungsmodule(self):
        if self.batteriemodule_ticket:
            return max(
                0,
                ceil((int(self.batteriemodule_ticket) + int(self.anz_speicher)) / 3)
                - ceil(int(self.batteriemodule_ticket) / 3),
            )
        else:
            return 0

    @property
    def leistung_ticket_preis(self):
        return self.calculate_price(
            OptionalAccessoriesPreise, "leistungsmodul", self.leistungsmodule
        )

    @property
    def notstrom_ticket_preis(self):
        return self.calculate_price(
            OptionalAccessoriesPreise, "backup_box", int(self.notstrom_ticket)
        )

    @property
    def eddi_ticket_preis(self):
        return self.calculate_price(
            OptionalAccessoriesPreise, "eddi", int(self.eddi_ticket)
        )

    @property
    def leistungsgewinn(self):
        return int(self.modulleistungWp) * int(self.modul_anzahl_ticket) / 1000

    @property
    def full_ticket_preis(self):
        return sum(
            filter(
                None,
                [
                    self.modul_ticket_preis,
                    self.optimizer_ticket_preis,
                    self.batterie_ticket_preis,
                    self.leistung_ticket_preis,
                    self.notstrom_ticket_preis,
                    self.eddi_ticket_preis,
                ],
            )
        )

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
            accessories_price += self.full_optimizer_preis
        if self.full_wallbox_preis:
            accessories_price += self.full_wallbox_preis
        if self.batteriespeicher_angebot_price:
            accessories_price += self.batteriespeicher_angebot_price
        if self.eddi:
            accessories_price += self.get_optional_accessory_price("eddi")
        if self.notstrom:
            accessories_price += self.get_optional_accessory_price("backup_box")
        if self.hub_included == True:
            accessories_price += self.get_optional_accessory_price("hub")
        if self.wandhalterung_fuer_speicher_preis:
            accessories_price += float(self.wandhalterung_fuer_speicher_preis)
        return accessories_price

    @property
    def angebots_summe(self):
        def get_price(prefix, kw):
            name = prefix + str(kw)

            return float(ModulePreise.objects.get(name=name).price)

        def get_garantie_price(kw, years):
            name = f"garantie{kw}_{years}"
            return float(ModuleGarantiePreise.objects.get(name=name).price)

        limits = [5, 7, 10, 12, 15, 20, 25]
        ranges = (
            [(0, limits[0])]
            + list(zip(limits, limits[1:]))
            + [(limits[-1], float("30"))]
        )

        angebotsSumme = sum(
            (min(self.modulsumme_kWp, upper) - lower) * get_price("Preis", upper)
            for lower, upper in ranges
            if lower < self.modulsumme_kWp
        )

        if self.user.typ == "Evolti":  # type: ignore
            angebotsSumme *= 1.05

        angebotsSumme *= float(self.get_komplexity)
        angebotsSumme += float(self.full_accessories_price)

        if self.garantieWR != "keine":
            garantie_years = int(self.garantieWR.split(" ")[0])
            garantie_kw = next(
                kw
                for kw in [3, 4, 5, 6, 8, 10, 15, 16, 20, 25, 30]
                if self.modulsumme_kWp <= kw
            )
            angebotsSumme += get_garantie_price(garantie_kw, garantie_years)

        if self.indiv_price_included:
            if self.user.typ == "Evolti":  # type: ignore
                angebotsSumme *= 1.07
            angebotsSumme = self.indiv_price

        userAufschlag = float(self.user.users_aufschlag) / 100 + 1  # type: ignore
        angebotsSumme *= userAufschlag

        return angebotsSumme

    @property
    def angebots_summe_mit_ticket_preis(self):
        summe = float(self.angebots_summe) + float(self.full_ticket_preis)
        return summe

    @property
    def kosten_pva(self):
        return float(self.angebots_summe) * float(
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
            "kunde": self.name,
            "adresse": self.full_adresse,
            "vertriebler": str(self.get_vertribler),
            "vertriebAbk": self.vertrieb_abk,
            "gueltig": self.angebot_gultig,
            "module": self.solar_module,
            "wpModule": self.modulleistungWp,
            "anzModule": self.modulanzahl,
            "produktGarantie": self.get_produktgarantie,
            "leistungsGarantie": self.get_leistungsgarantie,
            "kWp": self.modulsumme_kWp,
            "kWpOhneRundung": self.modulsumme_kWp,
            "standort": self.anlagen_standort,
            "garantieJahre": self.garantieWR,
            "batterieVorh": self.batteriespeicher_preis,
            "wandhalterungSpeicher": self.wandhalterung_fuer_speicher,
            "anzWandhalterungSpeicher": self.anz_wandhalterung_fuer_speicher,
            "wandhalterungSpeicherPreis": self.wandhalterung_fuer_speicher_preis,
            "batterieAnz": self.anz_speicher,
            "wallboxVorh": self.full_wallbox_preis,
            "wallboxTyp": self.wallboxtyp,
            "wallboxText": self.wallbox_text,
            "wallboxAnz": self.wallbox_anzahl,
            "optionVorh": self.notstrom,
            "eddi": self.eddi,
            "elwa": self.elwa,
            "thor": self.thor,
            "optimierer": self.optimizer,
            "anzOptimierer": self.anzOptimizer,
            "notstrom": self.notstrom,
            "solarModulePreis": self.solar_module_gesamt_preis,
            "wallboxPreis": self.full_wallbox_preis,
            "notstromPreis": self.get_optional_accessory_price("backup_box"),
            "batterieSpeicherPreis": self.batteriespeicher_preis,
            "gesamtOptimizerPreis": self.full_optimizer_preis,
            "eddiPreis": self.get_optional_accessory_price("eddi"),
            "angebotssumme": self.angebots_summe,
            "steuersatz": float(
                AndereKonfigurationWerte.objects.get(name="steuersatz").value
            ),
            "debug": False,
            "version": 1.0,
            "modulTicket": int(self.modul_anzahl_ticket),
            "optimizerTicket": int(self.optimizer_ticket),
            "batterieTicket": int(self.batteriemodule_ticket),
            "notstromTicket": int(self.notstrom_ticket),
            "eddiTicket": int(self.eddi_ticket),
            "gewinnTicket": self.leistungsgewinn,
            "modulTicketpreis": round(self.modul_ticket_preis, 2),
            "optimizerTicketpreis": round(self.optimizer_ticket_preis, 2),
            "batterieTicketpreis": round(self.batterie_ticket_preis, 2),
            "leistungTicketpreis": round(self.leistung_ticket_preis, 2),
            "notstromTicketpreis": round(self.notstrom_ticket_preis, 2),
            "eddiTicketpreis": round(self.eddi_ticket_preis, 2),
            "ticketPreis": round(self.full_ticket_preis, 2),
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
            "nutzEnergie": self.nutz_energie,
            "restenergie": self.restenergie,
            "reststromPreis": self.rest_strom_preis,
            "einspVerg": self.einsp_verg,
            "kostenPVA": self.kosten_pva,
            "ersparnis": self.ersparnis,
            "arbeitsListe": self.arbeits_liste,
            "restListe": self.rest_liste,
        }
        return dt
