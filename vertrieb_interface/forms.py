import json
import decimal
from dotenv import load_dotenv
from django import forms
from django.forms import ModelForm
from django.utils import timezone
from django.utils.formats import date_format
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from vertrieb_interface.get_user_angebots import update_status
from config.settings import ENV_FILE
from prices.models import SolarModulePreise, WallBoxPreise
from vertrieb_interface.models import VertriebAngebot
import re

now = timezone.now()
now_localized = timezone.localtime(now)
now_german = date_format(now_localized, "DATETIME_FORMAT")
load_dotenv(ENV_FILE)


from authentication.models import User


class ModulePreiseChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name}"  # type: ignore


VERTRIEB_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Privatkunden1"
BASE_URL = "https://creator.zoho.eu/api/v2/thomasgroebckmann/juno-kleinanlagen-portal/report/Elektrikkalender"
ACCESS_TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
LIMIT_ALL = 200
LIMIT_CURRENT = 10
MAX_RETRIES = 5
SLEEP_TIME = 1


def filter_hidden_choices(choices):
    HIDDEN_CHOICES = ["on Hold", "storniert", "abgelaufen", "abgelehnt", "angenommen"]
    return [(key, value) for key, value in choices if key not in HIDDEN_CHOICES]


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


def validate_german_mobile_number(value):
    if not re.match(r"^\+49(1[5-7][0-9])\d{7,8}$", value):
        raise ValidationError(
            "Geben Sie eine gültige deutsche Handynummer ein, die mit +49 beginnt."
        )


def validate_german_landline_number(value):
    if not re.match(r"^\+49\(\d{2,5}\)\d{3,}$", value):
        raise ValidationError(
            "Geben Sie eine gültige deutsche Festnetznummer ein, die mit +49 beginnt."
        )


def validate_name_format(value):
    # Regular expression for 'Last_Name First_Name Middle_Name(optional)'
    # Expecting each to start with a capital letter followed by lowercase letters
    # The middle name is optional and can be included
    if not re.match(
        r"^[A-ZÄÖÜ][a-zäöüß]+ [A-ZÄÖÜ][a-zäöüß]+(?: [A-ZÄÖÜ][a-zäöüß]+)?$", value
    ):
        raise ValidationError(
            "Format 'Nachname Vorname Mittelname (optional)', wobei jeder Name mit einem Großbuchstaben beginnt und deutsche Sonderzeichen enthält."
        )


def validate_two_decimal_places(value):
    # Check if the value is an instance of a valid number type
    if not isinstance(value, (int, float, decimal.Decimal)):
        raise ValidationError("Ungültige Eingabe: Der Wert muss eine Zahl sein.")

    try:
        decimal_value = decimal.Decimal(value)
    except decimal.InvalidOperation:
        raise ValidationError(
            "Ungültige Eingabe: Der Wert ist keine gültige Dezimalzahl."
        )

    if decimal_value.as_tuple().exponent < -2:
        raise ValidationError(
            "Achten Sie darauf, dass dieser Wert nicht mehr als zwei Dezimalstellen hat."
        )


def validate_floats(value):
    if not isinstance(value, float) or value < 0:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Eine gültige Gleitkommazahl größer oder gleich Null ist erforderlich."
            ),
            params={"value": value},
        )


def validate_integers(value):
    if not isinstance(value, int) or value < 0:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Eine gültige ganze Zahl größer oder gleich Null ist erforderlich."
            ),
            params={"value": value},
        )


def validate_integers_ticket(value):
    if not isinstance(value, int):
        raise ValidationError(
            ("Ungültige Eingabe: %(value)s. Die Menge muss ganzzahlig sein."),
            params={"value": value},
        )


def validate_solar_module_anzahl(value):
    if not isinstance(value, int) or not (6 <= value <= 69):
        raise ValidationError(
            "Ungültige Eingabe: %(value)s. Die Menge der Solarmodule sollte zwischen 6 und 69 liegen.",
            params={"value": value},
        )


def validate_solar_module_ticket_anzahl(value):
    if not isinstance(value, int) or value > 4:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Die Anzahl der Solarmodule sollte 4 oder weniger betragen."
            ),
            params={"value": value},
        )


def validate_optimizer_ticket_anzahl(value):
    if not isinstance(value, int) or value > 4:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Die Anzahl der Optimierer sollte 4 oder weniger betragen."
            ),
            params={"value": value},
        )


def validate_range(value, hersteller):
    # Define the maximum values for different hersteller
    max_values = {"Viessmann": 3, "default": 6}
    max_value = max_values.get(hersteller, max_values["default"])
    
    # Prepare the error messages
    error_messages = {
        "Viessmann": "Die Anzahl der Batteriespeicher Viessmann Vitocharge VX3 kann nicht mehr als 3 sein.",
        "default": "Ungültige Eingabe: %(value)s. Der gültige Bereich ist zwischen 0 und 6."
    }
    
    # Check if value is within the valid range
    if not isinstance(value, int) or not 0 <= value <= max_value:
        return error_messages.get(hersteller, error_messages["default"]), False
    return "", True

def validate_empty(value):
    if value is None or value == "":
        raise ValidationError(
            ("Ungültige Eingabe: %(value)s. Etwas hinzufügen"),
            params={"value": value},
        )


class VertriebAngebotEmailForm(ModelForm):
    email = forms.CharField(
        label="E-mail",
        max_length=100,
        required=False,
        validators=[validate_email],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_email",
                "style": "max-width: 300px",
            }
        ),
    )
    text_for_email = forms.CharField(
        label="Text for email",
        initial="""
            Sehr geehrter Interessent,

            anbei wie besprochen das Angebot im Anhang als PDF-Dokument.

            Bei Fragen stehen wir Ihnen gern jederzeit zur Verfügung!
            

            Wir wünschen Ihnen einen schönen Tag und würden uns über eine positive Rückmeldung freuen.

            Mit freundlichen Grüßen,

            Ihr Juno Solar Home Team
                """,
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 16,
                "class": "form-control",
                "id": "id_text_for_email",
            }
        ),
    )
    datenblatter_solar_module = forms.BooleanField(
        label="Datenblatter Solar Module",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "datenblatter_solar_module",
            }
        ),
    )
    datenblatter_speichermodule = forms.BooleanField(
        label="Datenblatter Speichermodule",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "datenblatter_speichermodule",
            }
        ),
    )
    datenblatter_wechselrichter = forms.BooleanField(
        label="Datenblatter Wechselrichter",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "datenblatter_wechselrichter",
            }
        ),
    )
    datenblatter_wallbox = forms.BooleanField(
        label="Datenblatter Wallbox",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "datenblatter_wallbox",
            }
        ),
    )
    datenblatter_backup_box = forms.BooleanField(
        label="Datenblatter Backup Box",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "datenblatter_backup_box",
            }
        ),
    )
    datenblatter_backup_box = forms.BooleanField(
        label="Datenblatter Optimierer",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "datenblatter_optimierer",
            }
        ),
    )

    class Meta:
        model = VertriebAngebot
        fields = [
            "email",
            "text_for_email",
            "datenblatter_solar_module",
            "datenblatter_speichermodule",
            "datenblatter_wechselrichter",
            "datenblatter_wallbox",
            "datenblatter_backup_box",
            "datenblatter_optimizer",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(VertriebAngebotEmailForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["email"].initial = self.instance.email
            self.fields["text_for_email"].initial = self.instance.text_for_email
            self.fields["datenblatter_solar_module"].initial = (
                self.instance.datenblatter_solar_module
            )
            self.fields["datenblatter_speichermodule"].initial = (
                self.instance.datenblatter_speichermodule
            )
            self.fields["datenblatter_wechselrichter"].initial = (
                self.instance.datenblatter_wechselrichter
            )
            self.fields["datenblatter_wallbox"].initial = (
                self.instance.datenblatter_wallbox
            )
            self.fields["datenblatter_backup_box"].initial = (
                self.instance.datenblatter_backup_box
            )
            self.fields["datenblatter_optimizer"].initial = (
                self.instance.datenblatter_optimizer
            )

    def save(self, commit=True):
        form = super(VertriebAngebotEmailForm, self).save(commit=False)
        if commit:
            form.save()
        return form


class VertriebAngebotEmptyForm(ModelForm):
    class Meta:
        model = VertriebAngebot
        fields = [
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
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        vertrieb_angebot = super().save(commit=False)
        if commit:
            vertrieb_angebot.save()
        return vertrieb_angebot


class VertriebAngebotForm(ModelForm):
    is_locked = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "is_locked",
            }
        ),
    )
    zoho_id = forms.IntegerField(required=False)

    angebot_id_assigned = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "angebot_id_assigned",
            }
        ),
    )
    status = forms.ChoiceField(
        label="Angebotstatus",
        choices=ANGEBOT_STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_status",
            }
        ),
        required=False,
    )
    status_change_date = forms.CharField(
        label="Angebotstatus Änderungsdatum:",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Angebotstatus Änderungsdatum:",
                "id": "status_change_date",
            }
        ),
    )

    zoho_kundennumer = forms.CharField(
        label="Kundennumer",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kundennumer",
                "id": "zoho_kundennumer",
            }
        ),
    )
    angebot_bekommen_am = forms.CharField(
        label="Bekommen am",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Angebot bekommen am",
                "id": "angebot_bekommen_am",
            }
        ),
    )
    ablehnungs_grund = forms.ChoiceField(
        choices=STORNIERUNGSGRUND_CHOICES,
        label="Grund für die Ablehnung des Auftrags",
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "ablehnungs_grund"}),
    )
    leadstatus = forms.ChoiceField(
        label="Leadstatus",
        choices=LEADSTATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "leadstatus"}),
        required=False,
    )

    ausrichtung_choices = (
        ("Süd", "Süd"),
        ("Ost/West", "Ost/West"),
    )
    komplex_choices = (
        ("einfach, einfach erreichbar", "einfach, einfach erreichbar"),
        ("einfach, schwer erreichbar", "einfach, schwer erreichbar"),
        ("komplex, einfach erreichbar", "komplex, einfach erreichbar"),
        ("komplex, schwer erreichbar", "komplex, schwer erreichbar"),
        ("sehr komplex", "sehr komplex"),
    )
    anrede = forms.ChoiceField(
        label="Anrede",
        choices=ANREDE_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_anrede",
            }
        ),
    )
    name = forms.ChoiceField(
        choices=[],
        label="Interessent",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control select2",
                "data-toggle": "select2",
                "id": "id_name",
                "style": "max-width: 300px",
            }
        ),
    )
    vorname_nachname = forms.CharField(
        label="Nach-, Vorname",
        required=False,
        
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_vorname_nachname",
            }
        ),
    )
    zoho_first_name = forms.CharField(
        label="Vorname",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_vorname",
            }
        ),
    )
    name_suffix = forms.CharField(
        label="Vorname Suffix",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_name_suffix",
            }
        ),
    )
    zoho_last_name = forms.CharField(
        label="Nachname",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_nachname",
            }
        ),
    )
    telefon_mobil = forms.CharField(
        label="Telefon Mobil",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Telefon Mobil",
                "id": "id_telefon_mobil",
            }
        ),
    )
    telefon_festnetz = forms.CharField(
        label="Telefon Festnetz",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Telefon Festnetz",
                "id": "id_telefon_festnetz",
            }
        ),
    )
    email = forms.CharField(
        label="E-mail",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email",
                "id": "id_email",
            }
        ),
    )
    firma = forms.CharField(
        label="Firma (optional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Firma",
                "id": "firma",
            }
        ),
    )
    strasse = forms.CharField(
        label="Straße & Hausnummer",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Straße & Hausnummer",
                "id": "id_strasse",
            }
        ),
    )
    ort = forms.CharField(
        label="PLZ & Ort",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "PLZ & Ort",
                "id": "id_ort",
            }
        ),
    )
    postanschrift_latitude = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "latitude",
            }
        ),
    )
    postanschrift_longitude = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "longitude",
            }
        ),
    )
    anlagenstandort = forms.CharField(
        label="Anlagenstandort (falls abweichend)",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Anlagenstandort",
                "id": "anlagenstandort",
            }
        ),
    )
    verbrauch = forms.FloatField(
        label="Strom Verbrauch [kWh]",
        initial=5000,
        required=False,
        validators=[validate_floats],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Strom Verbrauch [kWh]",
                "id": "id_verbrauch",
            }
        ),  # include your new validator here
    )
    grundpreis = forms.FloatField(
        label="Strom Grundpreis [€/Monat]",
        initial=11.4,
        validators=[validate_floats],
        required=True,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Strom Grundpreis [€/Monat]",
                "id": "grundpreis",
            }
        ),
    )
    arbeitspreis = forms.FloatField(
        label="Strom Arbeitspreis [ct/kWh]",
        initial=46,
        required=True,
        validators=[validate_floats],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Strom Arbeitspreis [ct/kWh]",
                "id": "arbeitspreis",
            }
        ),
    )
    prognose = forms.DecimalField(
        label="Prognose Strompreiserhöhung pro Jahr [%]",
        decimal_places=2,
        max_digits=10,
        initial=6,
        required=True,
        validators=[validate_two_decimal_places],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Prognose Strompreiserhöhung pro Jahr [%]",
                "id": "prognose",
            }
        ),
    )
    zeitraum = forms.IntegerField(
        label="Berechnungszeitraum [Jahre]",
        required=True,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Berechnungszeitraum [Jahre]",
                "id": "zeitraum",
            }
        ),
    )
    bis10kWp = forms.DecimalField(
        label="Einspeisevergütung bis 10 kWp",
        initial=8.2,
        decimal_places=2,
        max_digits=10,
        required=True,
        validators=[validate_two_decimal_places],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "bis10kWp"}),
    )
    bis40kWp = forms.DecimalField(
        label="Einspeisevergütung 10 bis 40 kWp",
        initial=7.1,
        decimal_places=2,
        max_digits=10,
        required=True,
        validators=[validate_two_decimal_places],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "bis40kWp"}),
    )

    anz_speicher = forms.IntegerField(
        label="Anzahl Speichermodule",
        required=False,
        initial=0,
        validators=[],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                
                "id": "anz_speicher",
            }
        ),
    )

    HERSTELLER_CHOICES = [
        ("----", "----"),
        ("Huawei", "Huawei"),
        ("Viessmann", "Viessmann"),
    ]

    WALLBOXTYP_CHOICES = [
        ("----", "----"),
        ("Huawei FusionCharge AC", "Huawei FusionCharge AC"),
        ("Viessmann Charging Station", "Viessmann Charging Station"),
    ]

    WECHSELRICHTER_MODEL_CHOICES = [
        ("----", "----"),
        ("SUN 2000", "SUN 2000"),
        ("Vitocharge VX3", "Vitocharge VX3"),
    ]

    SPEICHER_MODEL_CHOICES = [
        ("----", "----"),
        ("LUNA 2000", "LUNA 2000"),
        ("Vitocharge VX3 PV-Stromspeicher", "Vitocharge VX3 PV-Stromspeicher"),
    ]

    hersteller = forms.ChoiceField(
        label="Hersteller",
        required=True,
        choices=HERSTELLER_CHOICES,
        initial="Huawei",
        widget=forms.Select(attrs={"class": "form-select", "id": "hersteller"}),
    )

    wechselrichter_model = forms.ChoiceField(
        label="Wechselrichter",
        choices=WECHSELRICHTER_MODEL_CHOICES,
        required=True,
        initial="----",
        widget=forms.Select(
            attrs={"class": "form-select", "id": "wechselrichter_model"}
        ),
    )

    speicher_model = forms.ChoiceField(
        label="Batteriespeicher",
        choices=SPEICHER_MODEL_CHOICES,
        required=True,
        initial="----",
        widget=forms.Select(attrs={"class": "form-select", "id": "speicher_model"}),
    )

    gesamtkapazitat = forms.IntegerField(
        initial=0,
        label="Gesamtkapazitat",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "gesamtkapazitat",
                "readonly": "readonly",
            }
        ),
    )

    speicher = forms.BooleanField(
        label="Speichermodule inkl.",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "speicher",
            }
        ),
    )
    wandhalterung_fuer_speicher = forms.BooleanField(
        label="Wandhalterung für Speicher inkl.",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "wandhalterung_fuer_speicher",
            }
        ),
    )
    anz_wandhalterung_fuer_speicher = forms.IntegerField(
        label="Anzahl Wandhalterung",
        required=False,
        initial=0,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "anz_wandhalterung_fuer_speicher",
                "style": "max-width: 100px",
            }
        ),
    )
    wallbox = forms.BooleanField(
        label="E-Ladestation (Wallbox)",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "wallbox-checkbox",
                "style": "max-width: 300px",
            }
        ),
    )
    heizstab = forms.BooleanField(
        label="Heizstab für THOR inklusive",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "heizstab-checkbox",
                "style": "max-width: 300px",
            }
        ),
    )
    ausrichtung = forms.ChoiceField(
        label="Ausrichtung PV-Anlage",
        initial="Sud",
        choices=AUSRICHTUNG_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "ausrichtung",
                "style": "max-width: 150px",
            }
        ),
    )

    komplex = forms.ChoiceField(
        initial="sehr komplex",
        label="Komlexität",
        choices=komplex_choices,
        required=True,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "komplex", "style": "max-width: 300px"}
        ),
    )

    notizen = forms.CharField(
        label="Notizen",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 16,
                "class": "form-control",
                "id": "id_notizen",
            }
        ),
    )
    empfohlen_von = forms.CharField(
        label="Empfohlen von:",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Empfohlen von:",
                "id": "empfohlen_von",
            }
        ),
    )
    wallboxtyp = forms.ChoiceField(
        required=False,
        initial="----",
        choices=WALLBOXTYP_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "wallboxtyp",
                "style": "max-width: 300px",
            }
        ),
    )
    wallbox_anzahl = forms.IntegerField(
        initial=0,
        label="Anzahl",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "wallbox_anzahl",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    kabelanschluss = forms.FloatField(
        initial=10.0,
        label="Kabelanschlusslänge [m]",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "kabelanschluss",
                "style": "max-width: 300px",
            }
        ),
    )

    solar_module = forms.ChoiceField(
        label="Solar Module",
        widget=forms.Select(attrs={"class": "form-select", "id": "solar_module"}),
    )
    modulanzahl = forms.IntegerField(
        label="Module Anzahl",
        validators=[validate_solar_module_anzahl],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "modulanzahl",
                "data-toggle": "touchspin",
                "value": "0",
            }
        ),
    )
    garantieWR = forms.ChoiceField(
        choices=[
            ("10 Jahre", "10 Jahre"),
            ("15 Jahre", "15 Jahre"),
            ("20 Jahre", "20 Jahre"),
            ("25 Jahre", "25 Jahre"),
        ],
        initial="10 Jahre",
        widget=forms.Select(attrs={"class": "form-select", "id": "garantieWR"}),
    )
    eddi = forms.BooleanField(
        label="Eddi",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "eddi"}),
    )
    elwa = forms.BooleanField(
        label="AC-ELWA 2",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "elwa",
                "style": "max-width: 70px",
            }
        ),
    )
    thor = forms.BooleanField(
        label="AC-THOR",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "thor"}),
    )
    notstrom = forms.BooleanField(
        label="Notstrom",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "notstrom"}
        ),
    )

    zahlungsbedingungen = forms.ChoiceField(
        choices=[
            ("20 – 70 – 10 %", "20 – 70 – 10 %"),
            ("10 – 80 – 10 %", "10 – 80 – 10 %"),
            ("100 – 0 – 0 %", "100 – 0 – 0 %"),
        ],
        required=False,
        initial="20 – 70 – 10 %",
        widget=forms.Select(
            attrs={"class": "form-select", "id": "zahlungsbedingungen"}
        ),
    )

    anzOptimizer = forms.IntegerField(
        label="Optimizer Anzahl",
        required=True,
        validators=[validate_integers],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "anzOptimizer"}),
    )
    indiv_price_included = forms.BooleanField(
        label="Indiv. Preis",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "indiv_price_included"}
        ),
    )
    indiv_price = forms.FloatField(
        label="Individual Preis: ",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "indiv_price"}),
    )

    module_ticket = forms.ChoiceField(
        label="Zusätzlich & Abzüge: Module",
        choices=[
            ("Phono Solar PS420M7GFH-18/VNH", "Phono Solar PS420M7GFH-18/VNH"),
            (
                "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B",
                "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B",
            ),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "module_ticket"}),
    )

    modul_anzahl_ticket = forms.IntegerField(
        label="Module Anzahl",
        initial=0,
        required=False,
        validators=[validate_solar_module_ticket_anzahl],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "modul_anzahl_ticket"}
        ),
    )

    wandhalterung_fuer_speicher_ticket = forms.IntegerField(
        label="Wandhalterung für Batteriespeicher",
        initial=0,
        required=False,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "wandhalterung_fuer_speicher_ticket"}
        ),
    )
    optimizer_ticket = forms.IntegerField(
        label="Optimirer",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "optimizer_ticket"}
        ),
    )
    batteriemodule_ticket = forms.IntegerField(
        label="Batteriemodule",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "batteriemodule_ticket"}
        ),
    )
    notstrom_ticket = forms.IntegerField(
        label="Notstrom",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "notstrom_ticket"}
        ),
    )
    elwa_ticket = forms.IntegerField(
        label="ELWA 2",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "elwa_ticket"}),
    )
    thor_ticket = forms.IntegerField(
        label="AC THOR 2 3kW ",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "thor_ticket",
                "style": "max-width: 100px",
            }
        ),
    )
    heizstab_ticket = forms.IntegerField(
        label="Heizstab für THOR",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "heizstab_ticket",
                "style": "max-width: 100px",
            }
        ),
    )
    eddi_ticket = forms.IntegerField(
        label="Eddi ",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "eddi_ticket"}),
    )

    class Meta:
        model = VertriebAngebot
        fields = [
            "is_locked",
            "status",
            "anrede",
            "zoho_id",
            "telefon_festnetz",
            "telefon_mobil",
            "email",
            "vertriebler_display_value",
            "adresse_pva_display_value",
            "postanschrift_latitude",
            "postanschrift_longitude",
            "vertriebler_id",
            "notizen",
            "zoho_kundennumer",
            "angebot_bekommen_am",
            "status_change_date",
            "status_change_field",
            "ablehnungs_grund",
            "name",
            "vorname_nachname",
            "zoho_first_name",
            "name_suffix",
            "zoho_last_name",
            "firma",
            "strasse",
            "ort",
            "anlagenstandort",
            "verbrauch",
            "grundpreis",
            "arbeitspreis",
            "prognose",
            "zeitraum",
            "bis10kWp",
            "bis40kWp",
            "hersteller",
            "gesamtkapazitat",
            "wechselrichter_model",
            "speicher_model",
            "speicher",
            "anz_speicher",
            "wandhalterung_fuer_speicher",
            "anz_wandhalterung_fuer_speicher",
            "wallbox",
            "ausrichtung",
            "komplex",
            "wallboxtyp",
            "wallbox_anzahl",
            "kabelanschluss",
            "solar_module",
            "modulanzahl",
            "garantieWR",
            "zahlungsbedingungen",
            "elwa",
            "thor",
            # "heizstab",
            "eddi",
            "notstrom",
            "anzOptimizer",
            "indiv_price_included",
            "indiv_price",
            "module_ticket",
            "modul_anzahl_ticket",
            "elwa_ticket",
            "wandhalterung_fuer_speicher_ticket",
            "thor_ticket",
            "heizstab_ticket",
            "optimizer_ticket",
            "batteriemodule_ticket",
            "notstrom_ticket",
            "eddi_ticket",
        ]

    def __init__(self, *args, user, **kwargs):
        super(VertriebAngebotForm, self).__init__(*args, **kwargs)
        
        default_choice = [("", "--------")]
        try:
            profile = User.objects.get(zoho_id=user.zoho_id)
            data = json.loads(profile.zoho_data_text or "[]")

            # Filter out records with status "abgelehnt" or "storniert"
            data = [
                item
                for item in data
                if item["status"] not in ["abgelehnt", "storniert", "angenommen"]
            ]

            if data:
                name_list = [(item["name"], item["name"]) for item in data]
                name_list = sorted(name_list, key=lambda x: x[0])
                self.fields["name"].choices = default_choice + name_list
                name_to_kundennumer = {
                    item["name"]: item["zoho_kundennumer"] for item in data
                }

            else:
                # Set initial value to "-----" if there is no data
                self.fields["name"].initial = "-----"
        except User.DoesNotExist:
            # Handle case where the user does not exist
            self.fields["name"].initial = "-----"

        # profile = User.objects.get(zoho_id=user.zoho_id)
        self.fields["solar_module"].choices = [
            (module.name, module.name)
            for module in SolarModulePreise.objects.filter(in_stock=True)
        ]
        self.fields["module_ticket"].choices = [
            (module.name, module.name)
            for module in SolarModulePreise.objects.filter(in_stock=True)
        ]

        self.fields["wallboxtyp"].widget.attrs.update({"id": "wallboxtyp"})
        self.fields["angebot_id_assigned"].widget.attrs.update(
            {"id": "angebot_id_assigned"}
        )
        self.fields["zahlungsbedingungen"].widget.attrs.update(
            {"id": "zahlungsbedingungen"}
        )
        self.fields["notizen"].widget.attrs.update({"id": "id_notizen"})
        self.fields["vorname_nachname"].widget.attrs.update(
            {"id": "id_vorname_nachname"}
        )
        self.fields["status"].widget.attrs.update({"id": "id_status"})
        self.fields["verbrauch"].widget.attrs.update({"id": "id_verbrauch"})
        self.fields["wallbox_anzahl"].widget.attrs.update({"id": "wallbox_anzahl"})
        self.fields["wallbox"].widget.attrs.update({"id": "wallbox-checkbox"})
        self.fields["postanschrift_latitude"].widget.attrs.update(
            {"id": "id_postanschrift_latitude"}
        )
        self.fields["postanschrift_longitude"].widget.attrs.update(
            {"id": "id_postanschrift_longitude"}
        )

        self.fields["kabelanschluss"].widget.attrs.update({"id": "kabelanschluss"})
        self.fields["wandhalterung_fuer_speicher"].widget.attrs.update(
            {"id": "wandhalterung_fuer_speicher"}
        )
        self.fields["anz_wandhalterung_fuer_speicher"].widget.attrs.update(
            {"id": "anz_wandhalterung_fuer_speicher"}
        )
        self.fields["zoho_kundennumer"].widget.attrs.update({"id": "zoho_kundennumer"})
        self.fields["indiv_price_included"].widget.attrs.update(
            {"id": "indiv_price_included-checkbox"}
        )
        self.fields["email"].widget.attrs.update({"id": "id_email"})
        self.fields["gesamtkapazitat"].widget.attrs.update({"id": "id_gesamtkapazitat"})


    

    def save(self, commit=True):
        form = super(VertriebAngebotForm, self).save(commit=False)

        # Check if status is 'bekommen'

        if form.status == "bekommen":
            try:
                # Try to get the object from the database
                db_object = VertriebAngebot.objects.get(angebot_id=form.angebot_id)
                vertrieb_angebot = db_object
                db_countdown_on = db_object.countdown_on
                db_zoho_id = db_object.zoho_id
                if db_countdown_on == False:
                    form.status = "bekommen"
                    form.is_locked = True
                    now = timezone.now()
                    now_localized = timezone.localtime(now)
                    form.status_change_field = now_localized
                    form.status_change_date = timezone.now().date().isoformat()
                    db_object.countdown_on = True
                    if db_zoho_id:
                        update_status(db_zoho_id, form.status)
                    # post_angebot_to_zoho(form)
                    db_object.save()
                    form.save()

                if db_countdown_on == True:
                    form.status_change_date = db_object.status_change_date
                    form.status_change_field = db_object.status_change_field
                    form.save()

            except VertriebAngebot.DoesNotExist:
                pass

            form.save()
        else:
            form.status_change_date = None
            form.status_change_field = None
            form.save()

        if commit:
            form.save()

        return form

    def clean(self):
        cleaned_data = super().clean()

        # Define a dictionary to map incompatible combinations
        incompatible_combinations = {
            ("Viessmann", "Huawei FusionCharge AC"): "wallboxtyp",
            ("Viessmann", "SUN 2000"): "wechselrichter_model",
            ("Viessmann", "LUNA 2000"): "speicher_model",
            ("Huawei", "Viessmann Charging Station"): "wallboxtyp",
            ("Huawei", "Vitocharge VX3"): "wechselrichter_model",
            ("Huawei", "Vitocharge VX3 PV-Stromspeicher"): "speicher_model",
        }

        action = self.data.get("action_type")

        if action == "angebotsumme_rechnen":
            return cleaned_data

        interessent = cleaned_data.get("name")
        hersteller = cleaned_data.get("hersteller")
        wallboxtyp = cleaned_data.get("wallboxtyp")
        wechselrichter_model = cleaned_data.get("wechselrichter_model")
        speicher_model = cleaned_data.get("speicher_model")
        # kundennumer = cleaned_data.get("kundennumer")
        modulanzahl = cleaned_data.get("modulanzahl")
        vorname_nachname = cleaned_data.get("vorname_nachname")
        anzOptimizer = cleaned_data.get("anzOptimizer")
        anrede = cleaned_data.get("anrede")
        if anrede is None or anrede == "":
            raise ValidationError(
                ("Dieses Feld ist erforderlich"),
                params={"anrede": anrede},
            )
        if anrede != "Firma":
            # Perform validation for vorname_nachname if anrede is not "Firma"
            if not vorname_nachname:  # or any other validation you need
                raise ValidationError(
                    "Dieses Feld ist obligatorisch, es sei denn, 'Anrede' ist eine 'Firma'."
                )

        if anzOptimizer is not None and modulanzahl is not None:
            if anzOptimizer > modulanzahl:
                self.add_error(
                    "anzOptimizer",
                    ValidationError(
                        (
                            "Die Anzahl der Optimierer kann nicht größer sein als die Anzahl der Module."
                        ),
                        params={
                            "anzOptimizer": anzOptimizer,
                            "modulanzahl": modulanzahl,
                        },
                    ),
                )

            # Validation for 'name'
        name = cleaned_data.get("name")

        if name is None or interessent == "----":
            raise forms.ValidationError(
                {"interessent": "Sie haben keinen Interessent ausgewählt"}
            )

        if name == "":
            raise ValidationError(
                ("Dieses Feld ist erforderlich"),
                params={"name": name},
            )

        # Validation for 'vorname_nachname'

        if vorname_nachname is None or vorname_nachname == "":
            raise ValidationError(
                ("Dieses Feld ist erforderlich"),
                params={"vorname_nachname": vorname_nachname},
            )

        # Validation for 'strasse'
        strasse = cleaned_data.get("strasse")
        if strasse is None or strasse == "":
            raise ValidationError(
                ("Dieses Feld ist erforderlich"),
                params={"strasse": strasse},
            )

        # Validation for 'ort'
        ort = cleaned_data.get("ort")
        if ort is None or ort == "":
            raise ValidationError(
                ("Dieses Feld ist erforderlich"),
                params={"ort": ort},
            )

        email = self.cleaned_data.get("email")

        # Check if the email is empty
        if not email:
            raise ValidationError("Dieses Feld ist erforderlich")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError("Geben Sie eine gültige E-Mail-Adresse ein")

        speicher = cleaned_data.get("speicher")
        anz_speicher = cleaned_data.get("anz_speicher")
        message, is_valid = validate_range(anz_speicher, hersteller)
        if not is_valid:
            self.add_error('anz_speicher', ValidationError(message, params={'value': anz_speicher}))
        
        modul_anzahl_ticket = cleaned_data.get("modul_anzahl_ticket")
        if modul_anzahl_ticket is not None and modul_anzahl_ticket > 4:
            self.add_error(
                "modul_anzahl_ticket",
                ValidationError(
                    ("Die Anzahl der Ticket kann nicht mehr als 4 sein"),
                    params={
                        "modul_anzahl_ticket": modul_anzahl_ticket,
                    },
                ),
            )
        optimizer_ticket = cleaned_data.get("optimizer_ticket")
        if optimizer_ticket is not None and modul_anzahl_ticket is not None:
            if (
                optimizer_ticket > modul_anzahl_ticket
                or (modul_anzahl_ticket - optimizer_ticket) < 0
            ):
                self.add_error(
                    "modul_anzahl_ticket",
                    ValidationError(
                        ("Die Anzahl der Ticket kann nicht mehr als 4 sein"),
                        params={
                            "modul_anzahl_ticket": optimizer_ticket,
                        },
                    ),
                )

        wallbox = cleaned_data.get("wallbox")
        wallbox_anzahl = cleaned_data.get("wallbox_anzahl")

        if wallbox is not None and wallbox_anzahl is not None:
            if wallbox == True and wallbox_anzahl == 0:
                self.add_error(
                    "wallbox",
                    ValidationError(
                        (
                            "Die Anzahl der Wallbox kann nicht 0 sein wenn die E-Ladestation (Wallbox) inkl. is True."
                        ),
                        params={
                            "wallbox": wallbox,
                            "wallbox_anzahl": wallbox_anzahl,
                        },
                    ),
                )
        for (manufacturer, model), field_name in incompatible_combinations.items():
            if hersteller == manufacturer and cleaned_data.get(field_name) == model:
                raise forms.ValidationError(
                    {
                        field_name: f"Sie haben einen {manufacturer} Hersteller ausgewählt. Sie können keine {model.split()[0]} {field_name.replace('_', ' ')} auswählen. Überprüfen Sie die Daten."
                    }
                )

        if action == "save":
            return cleaned_data

        else:
            # hersteller = cleaned_data.get("hersteller")

            if interessent == "----":
                raise forms.ValidationError(
                    {"hersteller": "Sie haben keinen Hersteller ausgewählt"}
                )

            if hersteller == "----":
                raise forms.ValidationError(
                    {"hersteller": "Sie haben keinen Hersteller ausgewählt"}
                )
            return cleaned_data

    def clean_phone(self):
        telefon_mobil = self.cleaned_data["phone"]
        if len(telefon_mobil) != 11:
            raise forms.ValidationError(
                "Länge der Telefonnummer muss + und 10 Ziffern sein"
            )
        return telefon_mobil


class VertriebAngebotRechnerForm(VertriebAngebotForm):
    name = forms.ChoiceField(
        choices=[],
        label="Interessent",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control select2",
                "data-toggle": "select2",
                "id": "id_name",
                "style": "max-width: 300px",
            }
        ),
    )
    vorname_nachname = forms.CharField(
        label="Nach-, Vorname",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_vorname_nachname",
                "style": "max-width: 300px",
            }
        ),
    )
    telefon_mobil = forms.CharField(
        label="Telefon Mobil",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Telefon Mobil",
                "id": "id_telefon_mobil",
                "style": "max-width: 300px",
            }
        ),
    )
    telefon_festnetz = forms.CharField(
        label="Telefon Festnetz",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Telefon Festnetz",
                "id": "id_telefon_festnetz",
                "style": "max-width: 300px",
            }
        ),
    )
    email = forms.CharField(
        label="E-mail",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email",
                "id": "id_email",
                "style": "max-width: 300px",
            }
        ),
    )
    firma = forms.CharField(
        label="Firma (optional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Firma",
                "id": "firma",
                "style": "max-width: 300px",
            }
        ),
    )
    strasse = forms.CharField(
        label="Straße & Hausnummer",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Straße & Hausnummer",
                "id": "id_strasse",
                "style": "max-width: 300px",
            }
        ),
    )
    ort = forms.CharField(
        label="PLZ & Ort",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "PLZ & Ort",
                "id": "id_ort",
                "style": "max-width: 300px",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super(VertriebAngebotRechnerForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        action = self.data.get("action")

        # Bypass all further validations if the action is "angebotsumme_rechnen"
        if action == "angebotsumme_rechnen":
            return cleaned_data

        # Rest of your validation logic
        interessent = cleaned_data.get("name")
        modulanzahl = cleaned_data.get("modulanzahl")
        hersteller = cleaned_data.get("hersteller")

        if interessent == "----":
            # Add validation error or pass
            pass

        if hersteller == "----":
            # Add validation error or pass
            pass

        anrede = cleaned_data.get("anrede")
        if anrede is None or anrede == "":
            # Add validation error or pass
            pass

        return cleaned_data


class VertriebAngebotUpdateKalkulationForm(forms.ModelForm):
    class Meta:
        model = VertriebAngebot
        fields = [
            "verbrauch",
            "grundpreis",
            "arbeitspreis",
            "prognose",
            "zeitraum",
            "bis10kWp",
            "bis40kWp",
            "ausrichtung",
        ]


class UpdateAdminAngebotForm(forms.ModelForm):
    is_locked = forms.BooleanField(
        widget=forms.RadioSelect(choices=[(True, "Locked"), (False, "Unlocked")])
    )

    class Meta:
        model = VertriebAngebot
        fields = ["is_locked"]  # Add other fields as needed


class TicketForm(forms.ModelForm):
    name = forms.ChoiceField(
        choices=[],
        label="Interessent",
        required=True,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "id_name", "style": "max-width: 300px"}
        ),
    )
    module_ticket = forms.ChoiceField(
        label="Zusätzlich & Abzüge: Module",
        choices=[
            ("Phono Solar PS420M7GFH-18/VNH", "Phono Solar PS420M7GFH-18/VNH"),
            (
                "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B",
                "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B",
            ),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "module_ticket"}),
    )

    modul_anzahl_ticket = forms.IntegerField(
        label="Module Ticket-Anzahl",
        initial=0,
        required=False,
        validators=[validate_solar_module_ticket_anzahl],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "modul_anzahl_ticket"}
        ),
    )
    elwa_ticket = forms.IntegerField(
        label="ELWA 2",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "elwa_ticket"}),
    )
    thor_ticket = forms.IntegerField(
        label="AC THOR 2 3kW ",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "thor_ticket"}),
    )
    heizstab_ticket = forms.IntegerField(
        label="Heizstab ",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "heizstab_ticket"}
        ),
    )
    wandhalterung_fuer_speicher_ticket = forms.IntegerField(
        label="Wandhalterung für Batteriespeicher",
        initial=0,
        required=False,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "wandhalterung_fuer_speicher_ticket"}
        ),
    )
    optimizer_ticket = forms.IntegerField(
        label="Optimizer Ticket-Anzahl",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "optimizer_ticket"}
        ),
    )
    batteriemodule_ticket = forms.IntegerField(
        label="Batteriemodule Ticket-Anzahl",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "batteriemodule_ticket"}
        ),
    )
    notstrom_ticket = forms.IntegerField(
        label="Notstrom Ticket-Anzahl",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "notstrom_ticket"}
        ),
    )
    eddi_ticket = forms.IntegerField(
        label="Eddi Ticket-Anzahl",
        required=False,
        initial=0,
        validators=[validate_integers_ticket],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "eddi_ticket"}),
    )

    class Meta:
        model = VertriebAngebot
        fields = [
            "is_locked",
            "name",
            "module_ticket",
            "elwa_ticket",
            "wandhalterung_fuer_speicher_ticket",
            "thor_ticket",
            "heizstab_ticket",
            "modul_anzahl_ticket",
            "optimizer_ticket",
            "batteriemodule_ticket",
            "notstrom_ticket",
            "eddi_ticket",
        ]

    def __init__(self, *args, user, **kwargs):
        super(TicketForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if self.initial.get(field):
                self.fields[field].widget.attrs.update(
                    {"placeholder": self.initial[field]}
                )

    def save(self, commit=True):
        form = super(TicketForm, self).save(commit=False)
        if commit:
            form.save()
        return form

    def clean(self):
        cleaned_data = super().clean()
        modul_anzahl_ticket = cleaned_data.get("modul_anzahl_ticket")
        if modul_anzahl_ticket is not None and modul_anzahl_ticket > 4:
            self.add_error(
                "modul_anzahl_ticket",
                ValidationError(
                    ("Die Anzahl der Modul kann nicht mehr als 4 sein"),
                    params={
                        "modul_anzahl_ticket": modul_anzahl_ticket,
                    },
                ),
            )
