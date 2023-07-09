from django import forms
from django.forms import ModelForm
from matplotlib import widgets
from config.settings import ENV_FILE
import ast
from .models import VertriebAngebot
from django.core.exceptions import ValidationError
import decimal
import ast
from dotenv import load_dotenv, get_key
from django.utils import timezone
from django.utils import timezone
import json
from django.contrib.auth import get_user_model

load_dotenv(ENV_FILE)

User = get_user_model()

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

ANGEBOT_STATUS_CHOICES = [
    ("angenommen", "angenommen"),
    ("bekommen", "bekommen"),
    ("in Kontakt", "in Kontakt"),
    ("Kontaktversuch", "Kontaktversuch"),
    ("abgelehnt", "abgelehnt"),
    ("abgelaufen", "abgelaufen"),
]
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


# def get_names_from_string(names_string):
#     names_tuple = ast.literal_eval(names_string)
#     return names_tuple


# names_string = get_key(ENV_FILE, "NAMES_CHOICES")
# NAME_CHOICES = get_names_from_string(names_string)


def validate_two_decimal_places(value):
    decimal_value = decimal.Decimal(value)
    if decimal_value.as_tuple().exponent < -2:  # type: ignore
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


def validate_solar_module_anzahl(value):
    if value < 6:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Die Anzahl der Solarmodule sollte 6 oder mehr betragen."
            ),
            params={"value": value},
        )


def validate_solar_module_ticket_anzahl(value):
    if value > 4:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Die Anzahl der Solarmodule sollte 4 oder weniger betragen."
            ),
            params={"value": value},
        )


def validate_range(value):
    if not isinstance(value, int):
        if value < 0 or value > 6:
            raise ValidationError(
                ("Ungültige Eingabe: %(value)s. Der gültige Bereich ist 0-6."),
                params={"value": value},
            )


def validate_empty(value):
    if value is None or value == "":
        raise ValidationError(
            ("Ungültige Eingabe: %(value)s. Etwas hinzufügen"),
            params={"value": value},
        )


class VertriebAngebotForm(ModelForm):
    status = forms.ChoiceField(
        label="Angebotstatus",
        choices=ANGEBOT_STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_status",
                "style": "max-width: 200px",
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
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_anrede",
                "style": "max-width: 300px",
            }
        ),
    )
    name = forms.ChoiceField(
        choices=[],
        label="Name",
        required=True,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "id_name", "style": "max-width: 300px"}
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
        label="Email",
        max_length=100,
        required=True,
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
        required=True,
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
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "PLZ & Ort",
                "id": "id_ort",
                "style": "max-width: 300px",
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
                "style": "max-width: 300px",
            }
        ),
    )
    verbrauch = forms.FloatField(
        label="Strom Verbrauch [€/Monat]",
        initial=0.0,
        required=True,
        validators=[validate_floats],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_verbrauch",
            }
        ),  # include your new validator here
    )
    grundpreis = forms.FloatField(
        label="Strom Grundpreis [€/Monat]",
        initial=11.4,
        required=True,
        validators=[validate_floats],
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
        initial=30,
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
        initial=2.2,
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
        label="Anzahl Speichermodule (kann sein 0)",
        required=False,
        initial=0,
        validators=[validate_range],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Anzahl (kann sein 0 und <=6 )",
                "id": "anz_speicher",
                "style": "max-width: 100px",
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
                "style": "max-width: 300px",
            }
        ),
    )
    wallbox = forms.BooleanField(
        label="E-Ladestation (Wallbox)",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "wallbox",
                "style": "max-width: 300px",
            }
        ),
    )
    ausrichtung = forms.ChoiceField(
        label="Ausrichtung PV-Anlage",
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
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "class": "form-control",
                "style": "height: 150px",
                "style": "max-width: 800px",
                "id": "notizen",
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
        choices=[
            ("Pulsar Plus", "Pulsar Plus"),
            ("Pulsar Plus inkl. Power Boost", "Pulsar Plus inkl. Power Boost"),
            ("Commander 2", "Commander 2"),
            ("Commander 2 Inkl. Power Boost", "Commander 2 Inkl. Power Boost"),
        ],
        required=False,
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
                "type": "text",
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
                "data-toggle": "touchspin",
                "value": "10.0",
                "type": "text",
                "data-step": "0.1",
                "data-decimals": "2",
                "data-bts-postfix": "m",
                "style": "max-width: 300px",
            }
        ),
    )

    solar_module = forms.ChoiceField(
        label="Solar Module",
        choices=[
            ("Phono Solar PS420M7GFH-18/VNH", "Phono Solar PS420M7GFH-18/VNH"),
            (
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
            ),
        ],
        widget=forms.Select(attrs={"class": "form-select", "id": "solar_module"}),
    )
    modulanzahl = forms.IntegerField(
        label="Module Anzahl",
        initial=0,
        validators=[validate_solar_module_anzahl],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "modulanzahl",
                "data-toggle": "touchspin",
                "value": "0",
                "type": "text",
            }
        ),
    )
    garantieWR = forms.ChoiceField(
        choices=[
            ("keine", "keine"),
            ("15 Jahre", "15 Jahre"),
            ("20 Jahre", "20 Jahre"),
        ],
        initial="keine",
        widget=forms.Select(attrs={"class": "form-select", "id": "garantieWR"}),
    )
    eddi = forms.BooleanField(
        label="Eddi",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "eddi"}),
    )
    notstrom = forms.BooleanField(
        label="Notstrom",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "notstrom"}
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
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
                "Jinko Solar Tiger Neo N-type JKM420N-54HL4-B",
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
    optimizer_ticket = forms.IntegerField(
        label="Optimizer",
        required=False,
        initial=0,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "optimizer_ticket"}
        ),
    )
    batteriemodule_ticket = forms.IntegerField(
        label="Batteriemodule",
        required=False,
        initial=0,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "batteriemodule_ticket"}
        ),
    )
    notstrom_ticket = forms.IntegerField(
        label="Notstrom",
        required=False,
        initial=0,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "notstrom_ticket"}
        ),
    )
    eddi_ticket = forms.IntegerField(
        label="Eddi",
        required=False,
        initial=0,
        validators=[validate_integers],
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "eddi_ticket"}),
    )

    class Meta:
        model = VertriebAngebot
        fields = [
            "is_locked",
            "status",
            "anrede",
            "telefon_festnetz",
            "telefon_mobil",
            "email",
            "name",
            "vertriebler_display_value",
            "adresse_pva_display_value",
            "vertriebler_id",
            "notizen",
            "angebot_bekommen_am",
            "status_change_date",
            "ablehnungs_grund",
            "name",
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
            "speicher",
            "anz_speicher",
            "wallbox",
            "ausrichtung",
            "komplex",
            "wallboxtyp",
            "wallbox_anzahl",
            "kabelanschluss",
            "solar_module",
            "modulanzahl",
            "garantieWR",
            "eddi",
            "notstrom",
            "anzOptimizer",
            "indiv_price_included",
            "indiv_price",
            "module_ticket",
            "modul_anzahl_ticket",
            "optimizer_ticket",
            "batteriemodule_ticket",
            "notstrom_ticket",
            "eddi_ticket",
        ]

    def __init__(self, *args, user, **kwargs):
        super(VertriebAngebotForm, self).__init__(*args, **kwargs)
        profile = User.objects.get(zoho_id=user.zoho_id)

        data = json.loads(profile.zoho_data_text or '[["test", "test"]]')  # type: ignore
        name_list = [(item["name"], item["name"]) for item in data]
        name_list = sorted(name_list, key=lambda x: x[0])
        self.fields["name"].choices = name_list

        self.fields["wallbox"].widget.attrs.update({"id": "wallbox-checkbox"})
        self.fields["indiv_price_included"].widget.attrs.update(
            {"id": "indiv_price_included-checkbox"}
        )
        self.fields["indiv_price"].widget.attrs.update({"id": "indiv_price"})

        for field in self.fields:
            if self.initial.get(field):
                self.fields[field].widget.attrs.update(
                    {"placeholder": self.initial[field]}
                )

    def save(self, commit=True):
        form = super(VertriebAngebotForm, self).save(commit=False)
        # Check if status is 'bekommen' and status_change_date is empty
        if form.status == "bekommen" and not form.status_change_date:
            # Set status_change_date to the current date
            form.status_change_date = timezone.now().date().isoformat()
        if commit:
            form.save()
        return form

    def clean(self):
        cleaned_data = super().clean()

        modulanzahl = cleaned_data.get("modulanzahl")
        anzOptimizer = cleaned_data.get("anzOptimizer")
        anrede = cleaned_data.get("anrede")
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
        if anrede is None or anrede == "":
            raise ValidationError(
                ("Dieses Feld ist erforderlich"),
                params={"anrede": anrede},
            )
        speicher = cleaned_data.get("speicher")
        anz_speicher = cleaned_data.get("anz_speicher")
        if speicher == True and anz_speicher is not None:
            if anz_speicher <= 0: 
                self.add_error(
                    "anz_speicher",
                    ValidationError(
                        (
                            "Die Anzahl der Speicher kann nicht 0 seinwenn speicher inkl. = True"
                        ),
                        params={
                            "anz_speicher": anz_speicher,
                            "speicher": speicher,
                        },
                    ),
                )

    def clean_phone(self):
        telefon_mobil = self.cleaned_data["phone"]
        if len(telefon_mobil) != 11:
            raise forms.ValidationError(
                "Länge der Telefonnummer muss + und 10 Ziffern sein"
            )
        return telefon_mobil


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

    # @receiver(pre_save, sender=VertriebAngebot)
    # def handle_status_change(sender, instance, **kwargs):
    #     if instance.status is not None:
    #         old_instance = sender.objects.get(zoho_id=instance.zoho_id)
    #         if old_instance.status != instance.status and instance.status == 'bekommen':
    #             instance.status_change_date = timezone.now()

    #     else:
    #         instance.angebot_bekommen_am = timezone.now().date()

    # def clean_phone_2(self):
    #     telefon_festnetz = self.cleaned_data["phone"]
    #     if len(telefon_festnetz) != 11:
    #         raise forms.ValidationError(
    #             "Length of phone number must be + and 10 digits"
    #         )
    #     return telefon_festnetz
