from os import path
from django.db import models
from authentication.models import User
from shared.models import TimeStampMixin
from django.core.validators import MinValueValidator
from prices.models import (
    ModuleGarantiePreise,
    ModulePreise,
    OptionalAccessoriesPreise,
    AndereKonfigurationWerte,
    WallBoxPreise,
)
from django.contrib.auth import get_user_model
import datetime
from datetime import timedelta
from math import ceil


from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

User = get_user_model()


def get_price(model, name):
    model_name = model.__name__
    key = f"{model_name}_{name}"
    price = cache.get(key)
    if price is None:
        try:
            price = model.objects.get(name=name).price
        except ObjectDoesNotExist:
            price = 0
        cache.set(key, price)
    return price


# Model properties
MODULE_NAME_MAP = {
    "Phono Solar PS420M7GFH-18/VNH": "Phono Solar PS420M7GFH-18/VNH",
    "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B": "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
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
        choices=ANGEBOT_STATUS_CHOICES, max_length=255, blank=True, null=True
    )
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
    firma = models.CharField(max_length=100, blank=True)
    strasse = models.CharField(max_length=100, blank=True)
    ort = models.CharField(max_length=100, blank=True)
    anlagenstandort = models.CharField(max_length=100, blank=True, null=True)
    verbrauch = models.FloatField(
        default=5000, validators=[MinValueValidator(0)]  # type: ignore
    )
    grundpreis = models.FloatField(
        default=9.8, validators=[MinValueValidator(0)]  # type: ignore
    )
    arbeitspreis = models.FloatField(
        default=28.6, validators=[MinValueValidator(0)]  # type: ignore
    )
    prognose = models.FloatField(
        default=2.2, validators=[MinValueValidator(0)]  # type: ignore
    )
    zeitraum = models.PositiveIntegerField(default=5)
    bis10kWp = models.FloatField(
        default=8.20, validators=[MinValueValidator(0)]  # type: ignore
    )
    bis40kWp = models.FloatField(
        default=7.10, validators=[MinValueValidator(0)]  # type: ignore
    )
    speicher = models.BooleanField(default=False)
    anz_speicher = models.PositiveIntegerField(default=0)
    wallbox = models.BooleanField(default=False)
    ausrichtung = models.CharField(
        max_length=10, choices=AUSRICHTUNG_CHOICES, default="Ost/West"
    )
    komplex = models.CharField(
        max_length=30, choices=KOMPLEX_CHOICES, default="sehr komplex"
    )

    GARANTIE_WR_CHOICES = [
        ("keine", "keine"),
        ("15 Jahre", "15 Jahre"),
        ("20 Jahre", "20 Jahre"),
    ]
    solar_module = models.CharField(
        max_length=100,
        choices=[
            ("Phono Solar PS420M7GFH-18/VNH", "Phono Solar PS420M7GFH-18/VNH"),
            (
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
            ),
        ],
        default="Phono Solar PS420M7GFH-18/VNH",
    )
    modulleistungWp = models.PositiveIntegerField(default=420)
    modulanzahl = models.PositiveIntegerField(
        default=6, validators=[MinValueValidator(6)]
    )
    garantieWR = models.CharField(
        max_length=10, choices=GARANTIE_WR_CHOICES, default="keine"
    )
    eddi = models.BooleanField(default=False)
    notstrom = models.BooleanField(default=False)
    optimizer = models.BooleanField(default=False)
    anzOptimizer = models.PositiveIntegerField(default=0)

    wallboxtyp = models.CharField(
        max_length=100,
        choices=[
            ("Pulsar Plus", "Pulsar Plus"),
            ("Pulsar Plus inkl. Power Boost", "Pulsar Plus inkl. Power Boost"),
            ("Commander 2", "Commander 2"),
            ("Commander 2 Inkl. Power Boost", "Commander 2 Inkl. Power Boost"),
        ],
        blank=True,
        null=True,
    )
    wallbox_anzahl = models.PositiveIntegerField(default=0)
    kabelanschluss = models.FloatField(default=10.0, validators=[MinValueValidator(0)])
    hub_included = models.BooleanField(default=False)

    module_ticket = models.CharField(
        max_length=100,
        choices=[
            ("Phono Solar PS420M7GFH-18/VNH", "Phono Solar PS420M7GFH-18/VNH"),
            (
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
            ),
        ],
        blank=True,
        null=True,
    )
    modul_anzahl_ticket = models.PositiveIntegerField(default=0)
    optimizer_ticket = models.PositiveIntegerField(default=0)
    batteriemodule_ticket = models.PositiveIntegerField(default=0)
    notstrom_ticket = models.PositiveIntegerField(default=0)
    eddi_ticket = models.PositiveIntegerField(default=0)
    indiv_price_included = models.BooleanField(default=False)
    indiv_price = models.FloatField(default=0.00, validators=[MinValueValidator(0)])
    angebot_id_assigned = models.BooleanField(default=False)

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

    def get_optional_accessory_price(self, name):
        return float(OptionalAccessoriesPreise.objects.get(name=name).price)

    def get_module_preis(self, name):
        return float(ModulePreise.objects.get(name=name).price)

    def get_module_garantie_preis(self, name):
        return float(ModuleGarantiePreise.objects.get(name=name).price)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.angebot_id = self.generate_angebot_id()

        self.solar_module_angebot_price = (
            self.solar_module_gesamt_preis
            if self.solar_module_gesamt_preis is not None
            else 0.00
        )

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

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"AngebotID: {self.angebot_id}"

    def generate_angebot_id(self):
        user = User.objects.get(id=self.user.pk)
        kurz = user.kuerzel  # type: ignore
        current_datetime = datetime.datetime.now()
        return f"AN-{kurz}{current_datetime.strftime('%d%m%Y-%H%M%S')}"

    def get_absolute_url(self):
        return reverse("edit_angebot", args=[str(self.angebot_id)])

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
        if str(self.solar_module) == "Phono Solar PS420M7GFH-18/VNH":
            return "30 Jahre"
        elif str(self.solar_module) == "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B":
            return "0,4 % Jährliche Degradation"

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
        return {obj.name: obj.price for obj in ModulePreise.objects.all()}

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
    def solar_module_gesamt_preis(self):
        module_prices = self.get_module_prices()
        module_name = MODULE_NAME_MAP.get(
            self.solar_module, "Phono Solar PS420M7GFH-18/VNH"
        )  # Add default value
        if module_name in module_prices:
            return float(module_prices[module_name]) * int(self.modulanzahl)
        else:
            if self.modulanzahl and module_name:
                return float(module_prices[module_name]) * int(self.modulanzahl)
            else:
                return 0.00

    @property
    def batteriespeicher_preis(self):
        batteriePreis = 0
        if self.speicher == True:
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
        module_name = MODULE_NAME_MAP.get(self.solar_module)
        if module_name and (value := values.get(module_name + "_leistung")):
            return int(value * int(self.modulanzahl)) / 1000
        else:
            return 0

    @property
    def get_zuschlag(self):
        values = self.get_values()
        module_name = MODULE_NAME_MAP.get(
            self.solar_module, ""
        ).lower()  # Add default value
        return values.get(
            module_name, "Phono Solar PS420M7GFH-18/VNH"
        )  # Add default value

    @property
    def nutz_energie(self):
        nutzEnergie = float(self.verbrauch)
        if self.erzeugte_energie < nutzEnergie:
            nutzEnergie = float(self.erzProJahr) * float(self.modulsumme_kWp)
        if self.speicher:
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
            else ""
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
        return self.calculate_price(
            ModulePreise, "Phono-Solar", int(self.modul_anzahl_ticket)
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
        res = (
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
            "produktGarantie": self.garantieWR,
            "leistungsGarantie": self.get_leistungsgarantie,
            "kWp": self.modulsumme_kWp,
            "kWpOhneRundung": self.modulsumme_kWp,
            "standort": self.anlagen_standort,
            "garantieJahre": self.garantieWR,
            "batterieVorh": self.batteriespeicher_preis,
            "batterieAnz": self.anz_speicher,
            "wallboxVorh": self.full_wallbox_preis,
            "wallboxText": self.wallbox_text,
            "wallboxAnz": self.wallbox_anzahl,
            "optionVorh": self.notstrom,
            "eddi": self.eddi,
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
