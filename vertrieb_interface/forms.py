# Standard library imports
import decimal
import json, requests
import re

# Related third-party imports
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, MinValueValidator
from django.forms import ModelForm
from django.utils import timezone
from django.utils.formats import date_format
from dotenv import load_dotenv

# Local application/library specific imports
from authentication.models import User
from config.settings import ENV_FILE, GOOGLE_MAPS_API_KEY
from prices.models import SolarModulePreise, WallBoxPreise, AndereKonfigurationWerte, Sonderrabatt, WrTauschPreise
from vertrieb_interface.models import VertriebAngebot, VertriebTicket
from vertrieb_interface.zoho_api_connector import (
    update_status,
)

from vertrieb_interface.api_views.common import load_json_data, update_list
from vertrieb_interface.api_views.zoho_operations_aktualisierung import (
    load_user_angebots,
)

now = timezone.now()
now_localized = timezone.localtime(now)
now_german = date_format(now_localized, "DATETIME_FORMAT")
load_dotenv(ENV_FILE)


class KwpPreiseChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name}"  # type: ignore


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
            "Format 'Nachname, Vorname Mittelname (optional)', wobei jeder Name mit einem Großbuchstaben beginnt und deutsche Sonderzeichen enthält."
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
                f"Ungültige Eingabe: {value}. Eine gültige Gleitkommazahl größer oder gleich Null ist erforderlich."
        )


def validate_integers(value):
    if not isinstance(value, int) or value < 0:
        raise ValidationError(
                f"Ungültige Eingabe: {value}. Eine gültige ganze Zahl größer oder gleich Null ist erforderlich."
        )


def validate_integers_ticket(value):
    if not isinstance(value, int):
        raise ValidationError(
            f"Ungültige Eingabe: {value}. Die Menge muss ganzzahlig sein."
        )


def validate_rabatt(value):
    if self.instance.user.typ == "Kooperationspartner":
        rabatt_limit = 0
    elif self.instance.user.role.name != "admin" and self.instance.user.role.name != "manager":
        rabatt_limit = AndereKonfigurationWerte.objects.get(name="rabatt_limit").value
    else:
        rabatt_limit = 100
    if not isinstance(value, int) or not (0 <= value <= rabatt_limit):
        rabattStr = str(rabatt_limit).rstrip("0").rstrip(".")
        raise ValidationError(
            f"Ungültige Eingabe: {value}. Die Höhe des Rabatts sollte zwischen 0% und {rabattStr}% liegen."
        )


def validate_solar_module_anzahl(value):
    if not isinstance(value, int) or not (6 <= value <= 69):
        raise ValidationError(
            f"Ungültige Eingabe: {value}. Die Menge der Solarmodule sollte zwischen 6 und 69 liegen."
        )


def validate_solar_module_ticket_anzahl(value):
    if not isinstance(value, int) or value > 10:
        raise ValidationError(
                f"Ungültige Eingabe: {value}. Die Anzahl der Solarmodule sollte 10 oder weniger betragen."
        )


def validate_range(value, speicher_model, origAnzSpeicher=0):
    # Update the maximum values for different hersteller, including Huawei
    max_values = {"Vitocharge VX3 PV-Stromspeicher": 3, "LUNA 2000-5-S0": 6, "LUNA 2000-7-S1": 12, "ATMOCE M-ELV Akku MS-7K-U": 6, "default": 6}
    max_value = max_values.get(speicher_model, max_values["default"])

    # Update the error messages, including a specific message for Huawei
    error_messages = {
        "Vitocharge VX3 PV-Stromspeicher": f"Die Anzahl der Batteriespeicher Viessmann Vitocharge VX3 muss zwischen {-origAnzSpeicher} und {3-origAnzSpeicher} liegen.",
        "LUNA 2000-5-S0": f"Die Anzahl der Batteriespeicher von Huawei muss zwischen {-origAnzSpeicher} und {6-origAnzSpeicher} liegen.",
        "LUNA 2000-7-S1": f"Die Anzahl der Batteriespeicher von Huawei muss zwischen {-origAnzSpeicher} und {12-origAnzSpeicher} liegen.",
        "ATMOCE M-ELV Akku MS-7K-U": f"Die Anzahl der Batteriespeicher von Huawei muss zwischen {-origAnzSpeicher} und {6-origAnzSpeicher} liegen.",
        "default": f"Ungültige Eingabe: %(value)s. Der gültige Bereich ist zwischen {-origAnzSpeicher} und {6-origAnzSpeicher}.",
    }

    # Check if value is within the valid range
    # Note: For Huawei, we check if value is strictly less than 18, as per your condition
    if not isinstance(value, int) or not -origAnzSpeicher <= value <= max_values.get(
        speicher_model, max_value + 1
    ):
        # Use %(value)s for string interpolation in the default error message
        error_message = error_messages.get(speicher_model, error_messages["default"]) % {
            "value": value
        }
        return error_message, False
    return "", True


def validate_empty(value):
    if value is None or value == "":
        raise ValidationError(
            f"Ungültige Eingabe: {value}. Etwas hinzufügen"
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
    smtp_body = forms.CharField(
        label="Signatur",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 10,
                "class": "form-control",
                "id": "id_smtp_body",
                "disabled": True,
            }
        ),
    )
    salutation = forms.CharField(
        label="Anrede",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 1,
                "class": "form-control",
                "id": "id_salutation",
                "disabled": True,
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
    datenblatter_smartmeter = forms.BooleanField(
        label="Datenblatter Smart Meter",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "datenblatter_smartmeter",
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
            "smtp_body",
            "salutation",
            "datenblatter_solar_module",
            "datenblatter_speichermodule",
            "datenblatter_smartmeter",
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
            self.fields["smtp_body"].initial = self.instance.user.smtp_body
            self.fields["salutation"].initial = self.instance.salutation
            self.fields["datenblatter_solar_module"].initial = (
                self.instance.datenblatter_solar_module
            )
            self.fields["datenblatter_speichermodule"].initial = (
                self.instance.datenblatter_speichermodule
            )
            self.fields["datenblatter_smartmeter"].initial = (
                self.instance.datenblatter_smartmeter
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
            "ersatzstrom",
            "anzOptimizer",
            "wallboxtyp",
            "wallbox_anzahl",
            "kabelanschluss",
            "kabelSmartGuard",
            "rabatt"
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
    status_pva = forms.ChoiceField(
        label="Status_PVA",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_status_pva",
            }
        ),
        required=False,
    )
    angenommenes_angebot = forms.CharField(
        label="Angenommenes Angebot",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "angenommenes_angebot",
            }
        ),
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
    name_first_name = forms.CharField(
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
    name_last_name = forms.CharField(
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
    postanschrift = forms.CharField(
        label="Postanschrift Strasse",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Postanschrift",
                "id": "id_postanschrift",
            }
        ),
    )
    postanschrift_name = forms.CharField(
        label="Postanschrift (falls abweichend)",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Postanschrift Name",
                "id": "id_postanschrift_name",
            }
        ),
    )
    postanschrift_ort = forms.CharField(
        label="Postanschrift Ort & PLZ",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Postanschrift Ort",
                "id": "id_postanschrift_ort",
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
        label="Speichermodule Anzahl",
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
        ("Huawei FusionCharge AC", "Huawei FusionCharge AC"),
        ("Viessmann Charging Station", "Viessmann Charging Station"),
    ]


    WECHSELRICHTER_MODEL_CHOICES = [
        ("----", "----"),
        ("SUN 2000", "SUN 2000"),
        ("SUN 2000 MAP0", "SUN 2000 MAP0"),
        ("SUN 2000 MB0", "SUN 2000 MB0"),
        ("Vitocharge VX3", "Vitocharge VX3"),
    ]

    SPEICHER_MODEL_CHOICES = [
        ("----", "----"),
        ("LUNA 2000-7-S1", "LUNA 2000-7-S1"),
        ("LUNA 2000-5-S0", "LUNA 2000-5-S0"),
        ("ATMOCE M-ELV Akku MS-7K-U","ATMOCE M-ELV Akku MS-7K-U"),
        ("Vitocharge VX3 PV-Stromspeicher", "Vitocharge VX3 PV-Stromspeicher"),
    ]

    SMARTMETER_MODEL_CHOICES = [
        ("kein EMS", "kein EMS"),
        ("EMMA-A02", "EMMA-A02"),
        ("Smart Power Sensor DTSU666H", "Smart Power Sensor DTSU666H"),
        ("Viessmann Energiezähler", "Viessmann Energiezähler"),
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
        widget=forms.Select(
            attrs={"class": "form-select", "id": "wechselrichter_model"}
        ),
    )

    speicher_model = forms.ChoiceField(
        label="Batteriespeicher",
        choices=SPEICHER_MODEL_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "speicher_model"}),
    )

    smartmeter_model = forms.ChoiceField(
        label="EMS / Smart Meter",
        choices=SMARTMETER_MODEL_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "smartmeter_model"}),
    )

    gesamtkapazitat = forms.IntegerField(
        initial=0,
        label="Gesamtkapazität",
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
        label="Wandhalterung Anzahl",
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
        label="Komplexität",
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
        label="Wallbox",
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
        label="Wallbox Anzahl",
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
        initial=0.0,
        label="Kabelanschlusslänge >10m",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "kabelanschluss",
                "style": "max-width: 300px",
            }
        ),
    )
    kabelSmartGuard = forms.FloatField(
        initial=0.0,
        label="Kabel SmartGuard >10m",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "kabelSmartGuard",
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
                "style": "max-width: 300px",
            }
        ),
    )
    garantieWR = forms.ChoiceField(
        label="Garantie WR",
        choices=[
            ("10 Jahre", "10 Jahre"),
            ("15 Jahre", "15 Jahre"),
        ],
        initial="10 Jahre",
        widget=forms.Select(attrs={"class": "form-select", "id": "garantieWR"}),
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
        label="Notstrom Backupbox",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "notstrom"}
        ),
    )
    ersatzstrom = forms.BooleanField(
        label="SmartGuard inkl. EMMA",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "ersatzstrom"}
        ),
    )
    smartDongleLte = forms.BooleanField(
        label="Smart Dongle LTE",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "smartDongleLte"}
        ),
    )
    apzFeld = forms.BooleanField(
        label="APZ-Feld Nachrüstung in vorh. ZS",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "apzFeld"}),
    )
    apzFeldUVV = forms.BooleanField(
        label="APZ-Feld Nachrüstung mit UVV",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "apzFeldUVV"}),
    )
    zaehlerschrank = forms.BooleanField(
        label="Zählerschrankerneuerung nach TAB",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "zaehlerschrank"}),
    )
    potentialausgleich = forms.BooleanField(
        label="Potentialausgleich inkl. Erdspieß",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "potentialausgleich"}),
    )
    beta_platte = forms.BooleanField(
        label="Beta Platte",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "beta_platte"}),
    )
    metall_ziegel = forms.BooleanField(
        label="Metalldachziegel mit Modulhalter",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "metall_ziegel"}),
    )
    prefa_befestigung = forms.BooleanField(
        label="PREFA-Dachbefestigung",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "prefa_befestigung"}),
    )
    midZaehler = forms.IntegerField(
        label="MID-Zähler Anzahl",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "midZaehler",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    geruestKunde = forms.BooleanField(
        label="Gerüst durch Kunde",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "geruestKunde"}),
    )
    geruestOeffentlich = forms.BooleanField(
        label="Gerüst Traufhöhe höher 6m oder im öffentlichen Raum",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "geruestOeffentlich"}),
    )
    dachhakenKunde = forms.BooleanField(
        label="Setzen der Dachhaken durch Kunde",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "dachhakenKunde"}),
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
    rabatt = forms.IntegerField(
        initial=0,
        label="Rabatt in %",
        validators=[MinValueValidator(0)],
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "rabatt",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    ausweisung_rabatt = forms.BooleanField(
        label="Ausweisung Rabatt auf Angebot",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "ausweisung_rabatt"}),
    )
    wp_kombi_rabatt = forms.BooleanField(
        label="Rabatt nur mit Wärmepumpe",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "wp_kombi_rabatt"}),
    )
    sonderrabatt_included = forms.BooleanField(label="Sonderrabatt vorhanden",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "sonderrabatt_included"}),
    )
    sonderrabatt = forms.ChoiceField(
        label="Sonderrabatt",
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "sonderrabatt"}),
    )
    anzOptimizer = forms.IntegerField(
        label="Optimierer Anzahl",
        required=True,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "anzOptimizer",
                "style": "max-width: 300px",
            }
        ),
    )
    indiv_price_included = forms.BooleanField(
        label="Indiv. Preis",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "indiv_price_included"}
        ),
    )
    indiv_price = forms.FloatField(
        label="Individueller Preis: ",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "indiv_price"}),
    )
    indiv_text = forms.CharField(
        label="Individueller Text",
        max_length=200,
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows":5,
                "class": "form-control",
                "placeholder": "Individueller Text",
                "id": "id_indiv_text",
            }
        ),
    )
    # Finanzierung
    finanzierung = forms.BooleanField(
        label="Finanzierung",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "finanzierung"}),
    )
    anzahlung = forms.FloatField(
        label="Anzahlung",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "anzahlung"}),
    )
    monatliche_rate = forms.FloatField(
        label="Monatliche Rate",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "monatliche_rate"}),
    )
    laufzeit = forms.IntegerField(
        initial=0,
        label="Laufzeit",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "laufzeit",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    sollzinssatz = forms.FloatField(
        label="Sollzinssatz in %",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "sollzinssatz"}),
    )
    effektiver_zins = forms.FloatField(
        label="Effektiver Jahreszins in %",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "effektiver_zins"}),
    )
    gesamtkreditbetrag = forms.FloatField(
        label="Gesamtkreditbetrag",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "gesamtkreditbetrag"}),
    )

    class Meta:
        model = VertriebAngebot
        fields = [
            "is_locked",
            "status",
            "status_pva",
            "angenommenes_angebot",
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
            "name_first_name",
            "name_suffix",
            "name_last_name",
            "firma",
            "strasse",
            "ort",
            "postanschrift",
            "postanschrift_name",
            "postanschrift_ort",
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
            "smartmeter_model",
            "wandhalterung_fuer_speicher",
            "anz_wandhalterung_fuer_speicher",
            "wallbox",
            "ausrichtung",
            "komplex",
            "wallboxtyp",
            "wallbox_anzahl",
            "kabelanschluss",
            "kabelSmartGuard",
            "solar_module",
            "modulanzahl",
            "garantieWR",
            "elwa",
            "thor",
            "midZaehler",
            "apzFeld",
            "apzFeldUVV",
            "zaehlerschrank",
            "potentialausgleich",
            "beta_platte",
            "metall_ziegel",
            "prefa_befestigung",
            "heizstab",
            "notstrom",
            "ersatzstrom",
            "smartDongleLte",
            "anzOptimizer",
            "geruestKunde",
            "geruestOeffentlich",
            "dachhakenKunde",
            "indiv_price_included",
            "indiv_price",
            "indiv_text",
            "zahlungsbedingungen",
            "rabatt",
            "ausweisung_rabatt",
            "wp_kombi_rabatt",
            "sonderrabatt_included",
            "sonderrabatt",
            "finanzierung",
            "anzahlung",
            "monatliche_rate",
            "laufzeit",
            "sollzinssatz",
            "effektiver_zins",
            "gesamtkreditbetrag"
        ]

    def __init__(self, *args, user, **kwargs):
        super(VertriebAngebotForm, self).__init__(*args, **kwargs)
        default_choice = [("", "--------")]
        self.fields["name"].choices = default_choice  # Set default choice initially

        try:
            filtered_data = [
                item
                for item in load_json_data(user.zoho_data_text)
                if item["status"] not in ["abgelehnt", "storniert", "angenommen"]
            ]

            if filtered_data:
                name_list = [(item["zoho_id"], item["name"]) for item in filtered_data]
                name_list = sorted(name_list, key=lambda x: x[1])
                self.fields["name"].choices = default_choice + name_list

            else:
                self.fields["name"].choices = (
                    default_choice  # Only default choice available
                )
        except Exception as e:
            # Handle other exceptions which could be related to data issues or fetching problems

            self.fields["name"].choices = default_choice  # Fallback to default choice

        self.fields["solar_module"].choices = [
            (module.name, module.name)
            for module in SolarModulePreise.objects.filter(in_stock=True)
        ]
        self.fields["wallboxtyp"].choices = [
            (module.name, module.name)
            for module in WallBoxPreise.objects.filter(in_stock=True)
        ]
        self.fields["sonderrabatt"].choices = [
            (sonderrab.name, sonderrab.name)
            for sonderrab in Sonderrabatt.objects.filter(is_active=True)
        ]
        self.fields["wallboxtyp"].widget.attrs.update({"id": "wallboxtyp"})

        self.fields["angebot_id_assigned"].widget.attrs.update(
            {"id": "angebot_id_assigned"}
        )
        self.fields["zahlungsbedingungen"].widget.attrs.update(
            {"id": "zahlungsbedingungen"}
        )
        self.fields["rabatt"].widget.attrs.update(
            {"id": "rabatt"}
        )
        # self.fields["anzahlung"].widget.attrs.update({"id": "anzahlung"})
        # self.fields["monatliche_rate"].widget.attrs.update({"id": "monatliche_rate"})
        # self.fields["laufzeit"].widget.attrs.update({"id": "laufzeit"})
        # self.fields["sollzinssatz"].widget.attrs.update({"id": "sollzinssatz"})
        # self.fields["effektiver_zins"].widget.attrs.update({"id": "effektiver_zins"})
        self.fields["notizen"].widget.attrs.update({"id": "id_notizen"})
        self.fields["vorname_nachname"].widget.attrs.update(
            {"id": "id_vorname_nachname"}
        )

        self.fields["name_first_name"].widget.attrs.update({"id": "id_vorname"})
        self.fields["name_last_name"].widget.attrs.update({"id": "id_nachname"})
        self.fields["status"].widget.attrs.update({"id": "id_status"})
        self.fields["wechselrichter_model"].widget.attrs.update(
            {"id": "wechselrichter_model"}
        )
        self.fields["speicher_model"].widget.attrs.update({"id": "speicher_model"})
        self.fields["smartmeter_model"].widget.attrs.update({"id": "smartmeter_model"})
        self.fields["hersteller"].widget.attrs.update({"id": "hersteller"})
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
        self.fields["kabelSmartGuard"].widget.attrs.update({"id": "kabelSmartGuard"})
        self.fields["wandhalterung_fuer_speicher"].widget.attrs.update(
            {"id": "wandhalterung_fuer_speicher"}
        )
        self.fields["anz_wandhalterung_fuer_speicher"].widget.attrs.update(
            {"id": "anz_wandhalterung_fuer_speicher"}
        )
        self.fields["zoho_kundennumer"].widget.attrs.update({"id": "zoho_kundennumer"})

        self.fields["angenommenes_angebot"].widget.attrs.update(
            {"id": "angenommenes_angebot"}
        )
        self.fields["indiv_price_included"].widget.attrs.update(
            {"id": "indiv_price_included-checkbox"}
        )
        self.fields["email"].widget.attrs.update({"id": "id_email"})
        self.fields["gesamtkapazitat"].widget.attrs.update({"id": "id_gesamtkapazitat"})
        self.fields["name"].widget.attrs.update({"id": "id_name"})

    def save(self, commit=True):
        form = super(VertriebAngebotForm, self).save(commit=False)

        if form.status == "bekommen":
            try:
                db_object = VertriebAngebot.objects.get(angebot_id=form.angebot_id)
                db_countdown_on = db_object.countdown_on
                # db_zoho_id = db_object.zoho_id
                if db_countdown_on == False:
                    form.status = "bekommen"
                    form.is_locked = True
                    now = timezone.now()
                    now_localized = timezone.localtime(now)
                    form.status_change_field = now_localized
                    form.status_change_date = timezone.now().date().isoformat()
                    db_object.countdown_on = True
                    # moved the status change to happen in JPP on creation of Angebot
                    # if db_zoho_id:
                    #     update_status(db_zoho_id, form.status)
                    db_object.save()
                    form.save()
                else:
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
        incompatible_combinations = {
            ("Viessmann", "Huawei FusionCharge AC"): "wallboxtyp",
            ("Viessmann", "SUN 2000"): "wechselrichter_model",
            ("Viessmann", "SUN 2000 MAP0"): "wechselrichter_model",
            ("Viessmann", "SUN 2000 MB0"): "wechselrichter_model",
            ("Viessmann", "LUNA 2000-5-S0"): "speicher_model",
            ("Viessmann", "LUNA 2000-7-S1"): "speicher_model",
            ("Viessmann", "ATMOCE M-ELV Akku MS-7K-U"): "speicher_model",
            ("Viessmann", "Smart Power Sensor DTSU666H"): "smartmeter_model",
            ("Viessmann", "EMMA-A02"): "smartmeter_model",
            ("Huawei", "Viessmann Charging Station"): "wallboxtyp",
            ("Huawei", "Vitocharge VX3"): "wechselrichter_model",
            ("Huawei", "Vitocharge VX3 PV-Stromspeicher"): "speicher_model",
            ("Huawei", "Viessmann Energiezähler"): "smartmeter_model",
        }

        action = self.data.get("action_type")
        hersteller = cleaned_data.get("hersteller")
        wechselrichter_model = cleaned_data.get("wechselrichter_model")
        speicher_model = cleaned_data.get("speicher_model")
        modulanzahl = cleaned_data.get("modulanzahl")
        anzOptimizer = cleaned_data.get("anzOptimizer")
        anz_speicher = cleaned_data.get("anz_speicher")
        notstrom = cleaned_data.get("notstrom")
        ersatzstrom = cleaned_data.get("ersatzstrom")
        smartmeter_model = cleaned_data.get("smartmeter_model")
        message, is_valid = validate_range(anz_speicher, speicher_model)
        if not is_valid:
            self.add_error(
                "anz_speicher", ValidationError(message, params={"value": anz_speicher})
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
        if notstrom and ersatzstrom:
            self.add_error(
                "notstrom",
                ValidationError(
                    (
                        "Bei der Auswahl einer Notstrom Backupbox kann nicht der SmartGuard ausgewählt werden."
                    ),
                    params={
                        "notstrom": notstrom,
                        "ersatzstrom": ersatzstrom,
                    },
                ),
            )
        if ersatzstrom and smartmeter_model != "kein EMS":
            self.add_error(
                "ersatzstrom",
                ValidationError(
                    (
                        "Bei der Auswahl eines SmartGuard kann kein EMS / Smart Meter ausgewählt werden."
                    ),
                    params={
                        "smartmeter_model": smartmeter_model,
                        "ersatzstrom": ersatzstrom,
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
        rabatt = cleaned_data.get("rabatt")
        rabatt_limit = 100
        if rabatt:
            if self.instance.user.typ == "Kooperationspartner":
                rabatt_limit = 0
            elif self.instance.user.role.name != "admin" and self.instance.user.role.name != "manager":
                rabatt_limit = AndereKonfigurationWerte.objects.get(name="rabatt_limit").value
        if isinstance(rabatt, int) and not (0 <= rabatt <= rabatt_limit):
            rabattStr = str(rabatt_limit).rstrip("0").rstrip(".")
            raise ValidationError(
                (
                    f"Ungültige Eingabe: {rabatt}. Die Höhe des Rabatts sollte zwischen 0%% und {rabattStr}%% liegen."
                ),
                params={
                    "rabatt": rabatt,
                }
            )
        if action == "angebotsumme_rechnen":
            return cleaned_data

        interessent = cleaned_data.get("name")
        modulanzahl = cleaned_data.get("modulanzahl")
        name_last_name = cleaned_data.get("name_last_name")
        anzOptimizer = cleaned_data.get("anzOptimizer")

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

        if interessent == "----":
            raise forms.ValidationError(
                {"name": "Sie haben keinen Interessent ausgewählt"}
            )

        anrede = cleaned_data.get("anrede")
        if anrede is None or anrede == "":
            raise ValidationError(
                ("Anrede Feld ist erforderlich"),
                params={"anrede": anrede},
            )

        if not name_last_name or name_last_name == "":
            raise ValidationError(
                ("Nachname Feld ist erforderlich und darf nicht leer sein"),
                params={"name_last_name": name_last_name},
            )

        strasse = cleaned_data.get("strasse")
        if strasse is None or strasse == "":
            raise ValidationError(
                ("Strasse Feld ist erforderlich"),
                params={"strasse": strasse},
            )
        ort = cleaned_data.get("ort")
        if ort is None or ort == "":
            raise ValidationError(
                ("Ort Feld ist erforderlich"),
                params={"ort": ort},
            )

        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Email Feld ist erforderlich")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError("Geben Sie eine gültige E-Mail-Adresse ein")

        for (manufacturer, model), field_name in incompatible_combinations.items():
            if hersteller == manufacturer and cleaned_data.get(field_name) == model:
                raise forms.ValidationError(
                    {
                        field_name: f"Sie haben einen {manufacturer} Hersteller ausgewählt. Sie können keine {model.split()[0]} {field_name.replace('_', ' ')} auswählen. Überprüfen Sie die Daten."
                    }
                )

        midZaehler = cleaned_data.get("midZaehler")
        wallbox_typ = cleaned_data.get("wallboxtyp")
        if midZaehler is not None and midZaehler > 0 and wallbox_anzahl > 0 and (wallbox_typ == "Huawei FusionCharge AC" or wallbox_typ == "Viessmann Charging Station"):
            raise ValidationError(
                (
                    f"Sie haben eine Wallbox vom Typ {wallbox_typ} ausgewählt. Sie können keinen MID-Zähler auswählen. Überprüfen Sie die Daten."
                ),
                params={
                    "midZaehler": midZaehler,
                    "wallbox_typ": wallbox_typ,
                },
            )

        if action == "save" and anrede == "Firma":
            return cleaned_data

        elif action == "save" and anrede != "Firma":
            name_first_name = cleaned_data.get("name_first_name")
            if not name_first_name or name_first_name == "":
                raise ValidationError(
                    ("Vorname Feld ist erforderlich und kann nicht leer sein"),
                    params={"name_first_name": name_first_name},
                )
            return cleaned_data

        else:
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

    def fill_geo_coordinates(self):
        address = f"{self.cleaned_data['strasse']}, {self.cleaned_data['ort']}"
        api_key = GOOGLE_MAPS_API_KEY
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"

        response = requests.get(base_url, params={"address": address, "key": api_key})
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                location = data["results"][0]["geometry"]["location"]
                self.cleaned_data["postanschrift_latitude"] = location["lat"]
                self.cleaned_data["postanschrift_longitude"] = location["lng"]
                self.instance.postanschrift_latitude = location["lat"]
                self.instance.postanschrift_longitude = location["lng"]
            else:
                print("Geocoding API did not return any results.")

        else:
            print("Geocoding API request failed.")


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


class VertriebTicketForm(ModelForm):
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
    status_pva = forms.ChoiceField(
        label="Status_PVA",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_status_pva",
            }
        ),
        required=False,
    )
    angenommenes_angebot = forms.CharField(
        label="Angenommenes Angebot",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_angenommenes_angebot",
            }
        ),
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
    name_first_name = forms.CharField(
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
    name_last_name = forms.CharField(
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
    postanschrift = forms.CharField(
        label="Postanschrift Strasse",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Postanschrift",
                "id": "id_postanschrift",
            }
        ),
    )
    postanschrift_name = forms.CharField(
        label="Postanschrift (falls abweichend)",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Postanschrift Name",
                "id": "id_postanschrift_name",
            }
        ),
    )
    postanschrift_ort = forms.CharField(
        label="Postanschrift Ort & PLZ",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Postanschrift Ort",
                "id": "id_postanschrift_ort",
            }
        ),
    )
    anz_speicher = forms.IntegerField(
        label="Speichermodule Anzahl",
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

    WALLBOXTYP_CHOICES = [
        ("Huawei FusionCharge AC", "Huawei FusionCharge AC"),
        ("Viessmann Charging Station", "Viessmann Charging Station"),
    ]


    SPEICHER_MODEL_CHOICES = [
        ("----", "----"),
        ("LUNA 2000-7-S1", "LUNA 2000-7-S1"),
        ("LUNA 2000-5-S0", "LUNA 2000-5-S0"),
        ("ATMOCE M-ELV Akku MS-7K-U", "ATMOCE M-ELV Akku MS-7K-U"),
        ("Vitocharge VX3 PV-Stromspeicher", "Vitocharge VX3 PV-Stromspeicher"),
    ]

    SMARTMETER_MODEL_CHOICES = [
        ("kein EMS", "kein EMS"),
        ("EMMA-A02", "EMMA-A02"),
        ("Smart Power Sensor DTSU666H", "Smart Power Sensor DTSU666H"),
        ("Viessmann Energiezähler", "Viessmann Energiezähler"),
    ]

    speicher_model = forms.ChoiceField(
        label="Batteriespeicher",
        choices=SPEICHER_MODEL_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "speicher_model"}),
    )

    smartmeter_model = forms.ChoiceField(
        label="EMS / Smart Meter",
        choices=SMARTMETER_MODEL_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "smartmeter_model"}),
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
        label="Wandhalterung Anzahl",
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
        label="Wallbox",
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
        label="Wallbox Anzahl",
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
        initial=0.0,
        label="Kabelanschlusslänge >10m",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "kabelanschluss",
                "style": "max-width: 300px",
            }
        ),
    )
    kabelSmartGuard = forms.FloatField(
        initial=0.0,
        label="Kabel SmartGuard >10m",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "kabelSmartGuard",
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
        validators=[validate_solar_module_ticket_anzahl],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "modulanzahl",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    wr_tausch = forms.ChoiceField(
        required=False,
        label="Wechselrichtertausch",
        initial="Kein Tausch",
        choices=("Kein Tausch", "Kein Tausch"),
        widget=forms.Select(attrs={"class": "form-select", "id": "wr_tausch"}),
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
        label="Notstrom Backupbox",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "notstrom"}
        ),
    )
    ersatzstrom = forms.BooleanField(
        label="SmartGuard inkl. EMMA",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "ersatzstrom"}
        ),
    )
    smartDongleLte = forms.BooleanField(
        label="Smart Dongle LTE",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "smartDongleLte"}
        ),
    )
    apzFeld = forms.BooleanField(
        label="APZ-Feld Nachrüstung",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "apzFeld"}),
    )
    apzFeldUVV = forms.BooleanField(
        label="APZ-Feld Nachrüstung mit UVV",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "apzFeldUVV"}),
    )
    zaehlerschrank = forms.BooleanField(
        label="Zählerschrankerneuerung nach TAB",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "zaehlerschrank"}),
    )
    potentialausgleich = forms.BooleanField(
        label="Potentialausgleich inkl. Erdspieß",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "potentialausgleich"}),
    )
    beta_platte = forms.BooleanField(
        label="Beta Platte",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "beta_platte"}),
    )
    metall_ziegel = forms.BooleanField(
        label="Metalldachziegel mit Modulhalter",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "metall_ziegel"}),
    )
    prefa_befestigung = forms.BooleanField(
        label="PREFA-Dachbefestigung",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "prefa_befestigung"}),
    )
    midZaehler = forms.IntegerField(
        label="MID-Zähler Anzahl",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "midZaehler",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    geruestKunde = forms.BooleanField(
        label="Gerüst durch Kunde",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "geruestKunde"}),
    )
    geruestOeffentlich = forms.BooleanField(
        label="Gerüst Traufhöhe höher 6m oder im öffentlichen Raum",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "geruestOeffentlich"}),
    )
    dachhakenKunde = forms.BooleanField(
        label="Setzen der Dachhaken durch Kunde",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "dachhakenKunde"}),
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
    rabatt = forms.IntegerField(
        initial=0,
        label="Rabatt in %",
        validators=[MinValueValidator(0)],
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "rabatt",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    ausweisung_rabatt = forms.BooleanField(
        label="Ausweisung Rabatt auf Angebot",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "ausweisung_rabatt"}),
    )
    wp_kombi_rabatt = forms.BooleanField(
        label="Rabatt nur mit Wärmepumpe",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "wp_kombi_rabatt"}),
    )
    sonderrabatt_included = forms.BooleanField(label="Sonderrabatt vorhanden",
       required=False,
       widget=forms.CheckboxInput(
           attrs={"class": "form-check-input", "id": "sonderrabatt_included"}),
    )
    sonderrabatt = forms.ChoiceField(
        label="Sonderrabatt",
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "sonderrabatt"}),
    )
    anzOptimizer = forms.IntegerField(
        label="Optimierer Anzahl",
        required=True,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "anzOptimizer",
                "style": "max-width: 300px",
            }
        ),
    )
    indiv_price_included = forms.BooleanField(
        label="Indiv. Preis",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "indiv_price_included"}
        ),
    )
    indiv_price = forms.FloatField(
        label="Individueller Preis: ",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "indiv_price"}),
    )
    indiv_text = forms.CharField(
        label="Individueller Text",
        max_length=200,
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "class": "form-control",
                "placeholder": "Individueller Text",
                "id": "id_indiv_text",
            }
        ),
    )

    class Meta:
        model = VertriebAngebot
        fields = [
            "is_locked",
            "status",
            "status_pva",
            "angenommenes_angebot",
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
            "name",
            "vorname_nachname",
            "name_first_name",
            "name_suffix",
            "name_last_name",
            "firma",
            "strasse",
            "ort",
            "postanschrift",
            "postanschrift_name",
            "postanschrift_ort",
            "speicher_model",
            "speicher",
            "anz_speicher",
            "smartmeter_model",
            "wandhalterung_fuer_speicher",
            "anz_wandhalterung_fuer_speicher",
            "wallbox",
            "wallboxtyp",
            "wallbox_anzahl",
            "kabelanschluss",
            "kabelSmartGuard",
            "solar_module",
            "modulanzahl",
            "wr_tausch",
            "elwa",
            "thor",
            "midZaehler",
            "apzFeld",
            "apzFeldUVV",
            "zaehlerschrank",
            "potentialausgleich",
            "beta_platte",
            "metall_ziegel",
            "prefa_befestigung",
            "heizstab",
            "notstrom",
            "ersatzstrom",
            "smartDongleLte",
            "anzOptimizer",
            "geruestKunde",
            "geruestOeffentlich",
            "dachhakenKunde",
            "indiv_price_included",
            "indiv_price",
            "indiv_text",
            "rabatt",
            "ausweisung_rabatt",
            "wp_kombi_rabatt",
            "sonderrabatt_included",
            "sonderrabatt",
        ]

    def __init__(self, *args, user, **kwargs):
        super(VertriebTicketForm, self).__init__(*args, **kwargs)
        default_choice = [("", "--------")]
        self.fields["name"].choices = default_choice  # Set default choice initially

        try:
            filtered_data = [
                item
                for item in load_json_data(user.zoho_data_text)
                if item["status"] not in ["abgelehnt", "storniert"]
            ]

            if filtered_data:
                name_list = [(item["zoho_id"], item["name"]) for item in filtered_data]
                name_list = sorted(name_list, key=lambda x: x[1])
                self.fields["name"].choices = default_choice + name_list

            else:
                self.fields["name"].choices = (
                    default_choice  # Only default choice available
                )
        except Exception as e:
            # Handle other exceptions which could be related to data issues or fetching problems

            self.fields["name"].choices = default_choice  # Fallback to default choice

        self.fields["solar_module"].choices = [
            (module.name, module.name)
            for module in SolarModulePreise.objects.filter()
        ]
        self.fields["wr_tausch"].choices = [
            (wr.name, wr.name)
            for wr in WrTauschPreise.objects.filter()
        ]
        self.fields["wallboxtyp"].choices = [
            (module.name, module.name)
            for module in WallBoxPreise.objects.filter(in_stock=True)
        ]
        self.fields["sonderrabatt"].choices = [
            (sonderrab.name, sonderrab.name)
            for sonderrab in Sonderrabatt.objects.filter(is_active=True)
        ]
        self.fields["wallboxtyp"].widget.attrs.update({"id": "wallboxtyp"})

        self.fields["angebot_id_assigned"].widget.attrs.update(
            {"id": "angebot_id_assigned"}
        )
        self.fields["rabatt"].widget.attrs.update(
            {"id": "rabatt"}
        )
        self.fields["notizen"].widget.attrs.update({"id": "id_notizen"})
        self.fields["vorname_nachname"].widget.attrs.update(
            {"id": "id_vorname_nachname"}
        )

        self.fields["name_first_name"].widget.attrs.update({"id": "id_vorname"})
        self.fields["name_last_name"].widget.attrs.update({"id": "id_nachname"})
        self.fields["speicher_model"].widget.attrs.update({"id": "speicher_model"})
        self.fields["smartmeter_model"].widget.attrs.update({"id": "smartmeter_model"})
        self.fields["wallbox_anzahl"].widget.attrs.update({"id": "wallbox_anzahl"})
        self.fields["wallbox"].widget.attrs.update({"id": "wallbox-checkbox"})
        self.fields["postanschrift_latitude"].widget.attrs.update(
            {"id": "id_postanschrift_latitude"}
        )
        self.fields["postanschrift_longitude"].widget.attrs.update(
            {"id": "id_postanschrift_longitude"}
        )
        self.fields["kabelanschluss"].widget.attrs.update({"id": "kabelanschluss"})
        self.fields["kabelSmartGuard"].widget.attrs.update({"id": "kabelSmartGuard"})
        self.fields["wandhalterung_fuer_speicher"].widget.attrs.update(
            {"id": "wandhalterung_fuer_speicher"}
        )
        self.fields["anz_wandhalterung_fuer_speicher"].widget.attrs.update(
            {"id": "anz_wandhalterung_fuer_speicher"}
        )
        self.fields["zoho_kundennumer"].widget.attrs.update({"id": "zoho_kundennumer"})

        self.fields["angenommenes_angebot"].widget.attrs.update(
            {"id": "id_angenommenes_angebot"}
        )
        self.fields["indiv_price_included"].widget.attrs.update(
            {"id": "indiv_price_included-checkbox"}
        )
        self.fields["email"].widget.attrs.update({"id": "id_email"})
        self.fields["name"].widget.attrs.update({"id": "id_name"})

    def save(self, commit=True):
        form = super(VertriebTicketForm, self).save(commit=False)

        if form.status == "bekommen":
            try:
                db_object = VertriebTicket.objects.get(ticket_id=form.ticket_id)
                db_countdown_on = db_object.countdown_on
                # db_zoho_id = db_object.zoho_id
                if db_countdown_on == False:
                    form.status = "bekommen"
                    form.is_locked = True
                    now = timezone.now()
                    now_localized = timezone.localtime(now)
                    form.status_change_field = now_localized
                    form.status_change_date = timezone.now().date().isoformat()
                    db_object.countdown_on = True
                    # no status change for Tickets
                    # if db_zoho_id:
                    #     update_status(db_zoho_id, form.status)
                    db_object.save()
                    form.save()
                else:
                    form.status_change_date = db_object.status_change_date
                    form.status_change_field = db_object.status_change_field
                    form.save()

            except VertriebTicket.DoesNotExist:
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

        action = self.data.get("action_type")
        speicher_model = cleaned_data.get("speicher_model")
        solar_module = cleaned_data.get("solar_module")
        modulanzahl = cleaned_data.get("modulanzahl")
        anzOptimizer = cleaned_data.get("anzOptimizer")
        anz_speicher = cleaned_data.get("anz_speicher")
        notstrom = cleaned_data.get("notstrom")
        ersatzstrom = cleaned_data.get("ersatzstrom")
        smartmeter_model = cleaned_data.get("smartmeter_model")
        angenommenes_angebot = cleaned_data.get("angenommenes_angebot")
        origAngebot = None
        if VertriebAngebot.objects.filter(angebot_id=angenommenes_angebot):
            origAngebot = VertriebAngebot.objects.get(angebot_id=angenommenes_angebot)
        if origAngebot and origAngebot.speicher_model == speicher_model:
            message, is_valid = validate_range(anz_speicher, speicher_model, origAngebot.anz_speicher)
        else:
            message, is_valid = validate_range(anz_speicher, speicher_model)
        if not is_valid:
            self.add_error(
                "anz_speicher", ValidationError(message, params={"value": anz_speicher})
            )
        if origAngebot:
            if anzOptimizer is not None:
                origOptimizer = VertriebAngebot.objects.get(angebot_id=angenommenes_angebot).anzOptimizer
                if origOptimizer + anzOptimizer < 0:
                    self.add_error(
                        "anzOptimizer",
                        ValidationError(
                            (
                                "Die Anzahl der Optimierer kann nicht geringer sein als die ursprünglich angebotene Anzahl der Optimierer."
                            ),
                            params={
                                "anzOptimizer": anzOptimizer,
                            },
                        ),
                    )
            if modulanzahl is not None:
                origAngebot = VertriebAngebot.objects.get(angebot_id=angenommenes_angebot)
                if origAngebot.modulanzahl + modulanzahl < 0:
                    self.add_error(
                        "modulanzahl",
                        ValidationError(
                            (
                                "Die Anzahl der Module kann nicht geringer sein als die ursprünglich angebotene Anzahl der Module."
                            ),
                            params={
                                "modulanzahl": modulanzahl,
                            },
                        ),
                    )
                elif modulanzahl < 0 and origAngebot.solar_module != solar_module:
                    self.add_error(
                        "modulanzahl",
                        ValidationError(
                            (
                                "Die Anzahl der Module kann nicht geringer als 0 sein, wenn der Modultyp abweicht."
                            ),
                            params={
                                "modulanzahl": modulanzahl,
                            },
                        ),
                    )
            if anz_speicher is not None:
                origSpeicher = VertriebAngebot.objects.get(angebot_id=angenommenes_angebot).anz_speicher
                if origSpeicher + anz_speicher < 0:
                    self.add_error(
                        "anz_speicher",
                        ValidationError(
                            (
                                "Die Anzahl der Speichermodule kann nicht geringer sein als die ursprünglich angebotene Anzahl der Speichermodule."
                            ),
                            params={
                                "anz_speicher": anz_speicher,
                            },
                        ),
                    )
        else:
            if anzOptimizer is not None:
                if anzOptimizer < 0:
                    self.add_error(
                        "anzOptimizer",
                        ValidationError(
                            (
                                "Die Anzahl der Optimierer kann ohne ein ursprüngliches Angebot nicht geringer als 0 sein."
                            ),
                            params={
                                "anzOptimizer": anzOptimizer,
                            },
                        ),
                    )
            if modulanzahl is not None:
                if modulanzahl < 0:
                    self.add_error(
                        "modulanzahl",
                        ValidationError(
                            (
                                "Die Anzahl der Module kann ohne ein ursprüngliches Angebot nicht geringer als 0 sein."
                            ),
                            params={
                                "modulanzahl": modulanzahl,
                            },
                        ),
                    )
            if anz_speicher is not None:
                if anz_speicher < 0:
                    self.add_error(
                        "anz_speicher",
                        ValidationError(
                            (
                                "Die Anzahl der Speichermodule kann ohne ein ursprüngliches Angebot nicht geringer als 0 sein."
                            ),
                            params={
                                "anz_speicher": anz_speicher,
                            },
                        ),
                    )

        if notstrom and ersatzstrom:
            self.add_error(
                "notstrom",
                ValidationError(
                    (
                        "Bei der Auswahl einer Notstrom Backupbox kann nicht der SmartGuard ausgewählt werden."
                    ),
                    params={
                        "notstrom": notstrom,
                        "ersatzstrom": ersatzstrom,
                    },
                ),
            )
        if ersatzstrom and smartmeter_model != "kein EMS":
            self.add_error(
                "ersatzstrom",
                ValidationError(
                    (
                        "Bei der Auswahl eines SmartGuard kann kein EMS / Smart Meter ausgewählt werden."
                    ),
                    params={
                        "smartmeter_model": smartmeter_model,
                        "ersatzstrom": ersatzstrom,
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
        rabatt = cleaned_data.get("rabatt")
        rabatt_limit = 100
        if rabatt:
            if self.instance.user.typ == "Kooperationspartner":
                rabatt_limit = 0
            elif self.instance.user.role.name != "admin" and self.instance.user.role.name != "manager":
                rabatt_limit = AndereKonfigurationWerte.objects.get(name="rabatt_limit").value
        if isinstance(rabatt, int) and not (0 <= rabatt <= rabatt_limit):
            rabattStr = str(rabatt_limit).rstrip("0").rstrip(".")
            raise ValidationError(
                (
                    f"Ungültige Eingabe: {rabatt}. Die Höhe des Rabatts sollte zwischen 0%% und {rabattStr}%% liegen."
                ),
                params={
                    "rabatt": rabatt,
                }
            )
        if action == "angebotsumme_rechnen":
            return cleaned_data

        interessent = cleaned_data.get("name")
        name_last_name = cleaned_data.get("name_last_name")

        if interessent == "----":
            raise forms.ValidationError(
                {"name": "Sie haben keinen Interessent ausgewählt"}
            )

        anrede = cleaned_data.get("anrede")
        if anrede is None or anrede == "":
            raise ValidationError(
                ("Anrede Feld ist erforderlich"),
                params={"anrede": anrede},
            )

        if not name_last_name or name_last_name == "":
            raise ValidationError(
                ("Nachname Feld ist erforderlich und darf nicht leer sein"),
                params={"name_last_name": name_last_name},
            )

        strasse = cleaned_data.get("strasse")
        if strasse is None or strasse == "":
            raise ValidationError(
                ("Strasse Feld ist erforderlich"),
                params={"strasse": strasse},
            )
        ort = cleaned_data.get("ort")
        if ort is None or ort == "":
            raise ValidationError(
                ("Ort Feld ist erforderlich"),
                params={"ort": ort},
            )

        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Email Feld ist erforderlich")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError("Geben Sie eine gültige E-Mail-Adresse ein")

        midZaehler = cleaned_data.get("midZaehler")
        wallbox_typ = cleaned_data.get("wallboxtyp")
        if midZaehler is not None and midZaehler > 0 and wallbox_anzahl > 0 and (wallbox_typ == "Huawei FusionCharge AC" or wallbox_typ == "Viessmann Charging Station"):
            raise ValidationError(
                (
                    f"Sie haben eine Wallbox vom Typ {wallbox_typ} ausgewählt. Sie können keinen MID-Zähler auswählen. Überprüfen Sie die Daten."
                ),
                params={
                    "midZaehler": midZaehler,
                    "wallbox_typ": wallbox_typ,
                },
            )

        if action == "save" and anrede == "Firma":
            return cleaned_data

        elif action == "save" and anrede != "Firma":
            name_first_name = cleaned_data.get("name_first_name")
            if not name_first_name or name_first_name == "":
                raise ValidationError(
                    ("Vorname Feld ist erforderlich und kann nicht leer sein"),
                    params={"name_first_name": name_first_name},
                )
            return cleaned_data
        else:
            if interessent == "----":
                raise forms.ValidationError(
                    {"interessent": "Sie haben keinen Interessenten ausgewählt"}
                )
            return cleaned_data

    def clean_phone(self):
        telefon_mobil = self.cleaned_data["phone"]
        if len(telefon_mobil) != 11:
            raise forms.ValidationError(
                "Länge der Telefonnummer muss + und 10 Ziffern sein"
            )
        return telefon_mobil

    def fill_geo_coordinates(self):
        address = f"{self.cleaned_data['strasse']}, {self.cleaned_data['ort']}"
        api_key = GOOGLE_MAPS_API_KEY
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"

        response = requests.get(base_url, params={"address": address, "key": api_key})
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                location = data["results"][0]["geometry"]["location"]
                self.cleaned_data["postanschrift_latitude"] = location["lat"]
                self.cleaned_data["postanschrift_longitude"] = location["lng"]
                self.instance.postanschrift_latitude = location["lat"]
                self.instance.postanschrift_longitude = location["lng"]
            else:
                print("Geocoding API did not return any results.")

        else:
            print("Geocoding API request failed.")


class VertriebTicketEmailForm(ModelForm):
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
    smtp_body = forms.CharField(
        label="Signatur",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 10,
                "class": "form-control",
                "id": "id_smtp_body",
                "disabled": True,
            }
        ),
    )
    salutation = forms.CharField(
        label="Anrede",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 1,
                "class": "form-control",
                "id": "id_salutation",
                "disabled": True,
            }
        ),
    )

    class Meta:
        model = VertriebTicket
        fields = [
            "email",
            "text_for_email",
            "smtp_body",
            "salutation",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(VertriebTicketEmailForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["email"].initial = self.instance.email
            self.fields["text_for_email"].initial = self.instance.text_for_email
            self.fields["smtp_body"].initial = self.instance.user.smtp_body
            self.fields["salutation"].initial = self.instance.salutation

    def save(self, commit=True):
        form = super(VertriebTicketEmailForm, self).save(commit=False)
        if commit:
            form.save()
        return form
