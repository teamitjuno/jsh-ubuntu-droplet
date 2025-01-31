from django import forms
from django.contrib.auth.models import Group
from .models import User
import json
import decimal
from prices.models import SolarModulePreise, WallBoxPreise
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django import forms
from .models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import User
from django.utils.translation import gettext_lazy as _


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


def validate_integers_ticket(value):
    if not isinstance(value, int):
        raise ValidationError(
            ("Ungültige Eingabe: %(value)s. Die Menge muss ganzzahlig sein."),
            params={"value": value},
        )


def validate_solar_module_anzahl(value):
    if value < 6 or value > 70:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Die Menge der Solarmodule sollte zwischen 6 und 70 liegen."
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


class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar"]


class CertifikateUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["user_certifikate"]


class InitialAngebotDataViewForm(forms.ModelForm):
    INITIAL_AUSRICHTUNG_CHOICES = (
        ("Sud", "Sud"),
        ("Ost/West", "Ost/West"),
    )
    INITIAL_KOMPLEX_CHOICES = (
        ("einfach, einfach erreichbar", "einfach, einfach erreichbar"),
        ("einfach, schwer erreichbar", "einfach, schwer erreichbar"),
        ("komplex, einfach erreichbar", "komplex, einfach erreichbar"),
        ("komplex, schwer erreichbar", "komplex, schwer erreichbar"),
        ("sehr komplex", "sehr komplex"),
    )
    INITIAL_GARANTIE_WR_CHOICES = [
        ("keine", "keine"),
        ("10 Jahre", "10 Jahre"),
        ("15 Jahre", "15 Jahre"),
    ]
    MAP_NOTIZEN_CHOICES = [
        ("Map", "Map"),
        ("Notizen", "Notizen"),
    ]

    map_notizen_container_view = forms.ChoiceField(
        label="Karte oder Notizen anzeigen",
        initial="Map",
        choices=MAP_NOTIZEN_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_map_notizen_container_view",
                "style": "max-width: 150px",
            }
        ),
    )
    is_home_page = forms.BooleanField(
        label="Start Seite ist 'Angebot Erstellung'",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_is_home_page",
            }
        ),
    )
    records_fetch_limit = forms.IntegerField(
        label="Anzahl der zuletzt aktualisierten Datensätze von JPP",
        required=True,
        # validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_records_fetch_limit",
                "style": "max-width: 100px",
            }
        ),
    )

    initial_text_for_email = forms.CharField(
        label="Default Email-Text",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 16,
                "class": "form-control",
                "id": "id_initial_text_for_email",
            }
        ),
    )
    initial_ausrichtung = forms.ChoiceField(
        label="Ausrichtung PV-Anlage",
        initial="Sud",
        choices=INITIAL_AUSRICHTUNG_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_initial_ausrichtung",
                "style": "max-width: 150px",
            }
        ),
    )

    initial_komplex = forms.ChoiceField(
        initial="sehr komplex",
        label="Komplexität",
        choices=INITIAL_KOMPLEX_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_initial_komplex",
                "style": "max-width: 300px",
            }
        ),
    )

    initial_solar_module = forms.ChoiceField(
        label="Solar Module",
        widget=forms.Select(
            attrs={"class": "form-select", "id": "id_initial_solar_module"}
        ),
    )
    initial_modulanzahl = forms.IntegerField(
        label="Module Anzahl",
        initial=0,
        validators=[validate_solar_module_anzahl],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_initial_modulanzahl",
                "data-toggle": "touchspin",
                "value": "0",
            }
        ),
    )
    initial_garantieWR = forms.ChoiceField(
        label="GarantieWR",
        choices=[
            ("10 Jahre", "10 Jahre"),
            ("15 Jahre", "15 Jahre"),
        ],
        initial="10 Jahre",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_initial_garantieWR",
                "style": "max-width: 300px",
            }
        ),
    )

    initial_wallboxtyp = forms.ChoiceField(
        label="Wallbox",
        choices=[],
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_initial_wallboxtyp",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_anz_speicher = forms.IntegerField(
        label="Speichermodule Anzahl",
        required=False,
        initial=0,
        validators=[validate_range],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Anzahl (kann sein 0 und <=6 )",
                "id": "id_initial_anz_speicher",
                "style": "max-width: 100px",
            }
        ),
    )
    initial_wandhalterung_fuer_speicher = forms.BooleanField(
        label="Wandhalterung für Speicher inkl.",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_initial_wandhalterung_fuer_speicher",
            }
        ),
    )
    initial_wallbox_anzahl = forms.IntegerField(
        initial=0,
        label="Wallbox Anzahl",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_initial_wallbox_anzahl",
                "data-toggle": "touchspin",
                "value": "0",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_kabelanschluss = forms.FloatField(
        initial=10.0,
        label="Kabelanschlusslänge [m]",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_initial_kabelanschluss",
                "style": "max-width: 300px",
            }
        ),
    )
    # initial_elwa = forms.BooleanField(
    #     label="AC-ELWA 2",
    #     required=False,
    #     widget=forms.CheckboxInput(
    #         attrs={
    #             "class": "form-check-input",
    #             "id": "id_initial_elwa",
    #             "style": "max-width: 70px",
    #         }
    #     ),
    # )
    initial_thor = forms.BooleanField(
        label="AC-THOR",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "id_initial_thor"}
        ),
    )
    initial_heizstab = forms.BooleanField(
        label="Heizstab für THOR inklusive",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_initial_heizstab",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_notstrom = forms.BooleanField(
        label="Notstrom",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "id_initial_notstrom"}
        ),
    )
    initial_anzOptimizer = forms.IntegerField(
        label="Optimierer Anzahl",
        required=True,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "id_initial_anzOptimizer"}
        ),
    )
    initial_verbrauch = forms.FloatField(
        label="Strom Verbrauch [kWh]",
        required=False,
        validators=[validate_floats],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Strom Verbrauch [kWh]",
                "id": "id_initial_verbrauch",
                "style": "max-width: 300px",
            }
        ),  # include your new validator here
    )
    initial_grundpreis = forms.FloatField(
        label="Strom Grundpreis [€/Monat]",
        initial=11.4,
        required=True,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Strom Grundpreis [€/Monat]",
                "id": "id_initial_grundpreis",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_arbeitspreis = forms.FloatField(
        label="Strom Arbeitspreis [ct/kWh]",
        initial=46,
        required=True,
        validators=[validate_floats],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Strom Arbeitspreis [ct/kWh]",
                "id": "id_initial_arbeitspreis",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_prognose = forms.DecimalField(
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
                "id": "id_initial_prognose",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_zeitraum = forms.IntegerField(
        label="Berechnungszeitraum [Jahre]",
        required=True,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Berechnungszeitraum [Jahre]",
                "id": "id_initial_zeitraum",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_bis10kWp = forms.DecimalField(
        label="Einspeisevergütung bis 10 kWp",
        initial=8.2,
        decimal_places=2,
        max_digits=10,
        required=True,
        validators=[validate_two_decimal_places],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_initial_bis10kWp",
                "style": "max-width: 300px",
            }
        ),
    )
    initial_bis40kWp = forms.DecimalField(
        label="Einspeisevergütung 10 bis 40 kWp",
        initial=7.1,
        decimal_places=2,
        max_digits=10,
        required=True,
        validators=[validate_two_decimal_places],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_initial_bis40kWp",
                "style": "max-width: 300px",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "is_home_page",
            "map_notizen_container_view",
            "initial_verbrauch",
            "initial_grundpreis",
            "initial_arbeitspreis",
            "initial_prognose",
            "initial_zeitraum",
            "initial_bis10kWp",
            "initial_bis40kWp",
            "initial_anz_speicher",
            "initial_wandhalterung_fuer_speicher",
            "initial_ausrichtung",
            "initial_komplex",
            "initial_solar_module",
            "initial_modulanzahl",
            "initial_garantieWR",
            # "initial_elwa",
            "initial_thor",
            "initial_heizstab",
            "initial_notstrom",
            "initial_anzOptimizer",
            "initial_wallboxtyp",
            "initial_wallbox_anzahl",
            "initial_kabelanschluss",
            "initial_text_for_email",
            "top_verkaufer_container_view",
            "profile_container_view",
            "activity_container_view",
            "angebot_statusubersicht_view",
            "pv_rechner_view",
            "anzahl_sol_module_view",
            "records_fetch_limit",
            "smtp_body",
        ]

    def __init__(self, *args, user, **kwargs):
        super(InitialAngebotDataViewForm, self).__init__(*args, **kwargs)

        self.fields["initial_solar_module"].choices = [
            (module.name, module.name)
            for module in SolarModulePreise.objects.filter(in_stock=True)
        ]
        self.fields["initial_wallboxtyp"].choices = [
            (module.name, module.name)
            for module in WallBoxPreise.objects.filter(in_stock=True)
        ]
        self.fields["map_notizen_container_view"].widget.attrs.update(
            {"id": "id_map_notizen_container_view"}
        )
        self.fields["is_home_page"].widget.attrs.update({"id": "id_is_home_page"})
        self.fields["initial_verbrauch"].widget.attrs.update(
            {"id": "id_initial_verbrauch"}
        )
        self.fields["initial_grundpreis"].widget.attrs.update(
            {"id": "id_initial_grundpreis"}
        )
        self.fields["initial_arbeitspreis"].widget.attrs.update(
            {"id": "id_initial_arbeitspreis"}
        )
        self.fields["initial_prognose"].widget.attrs.update(
            {"id": "id_initial_prognose"}
        )
        self.fields["initial_zeitraum"].widget.attrs.update(
            {"id": "id_initial_zeitraum"}
        )
        self.fields["initial_bis10kWp"].widget.attrs.update(
            {"id": "id_initial_bis10kWp"}
        )
        self.fields["initial_bis40kWp"].widget.attrs.update(
            {"id": "id_initial_bis40kWp"}
        )
        self.fields["initial_anz_speicher"].widget.attrs.update(
            {"id": "id_initial_anz_speicher"}
        )
        self.fields["initial_wandhalterung_fuer_speicher"].widget.attrs.update(
            {"id": "id_initial_wandhalterung_fuer_speicher"}
        )
        self.fields["initial_ausrichtung"].widget.attrs.update(
            {"id": "id_initial_ausrichtung"}
        )
        self.fields["initial_komplex"].widget.attrs.update({"id": "id_initial_komplex"})
        self.fields["initial_solar_module"].widget.attrs.update(
            {"id": "id_initial_solar_module"}
        )
        self.fields["initial_modulanzahl"].widget.attrs.update(
            {"id": "id_initial_modulanzahl"}
        )
        self.fields["initial_garantieWR"].widget.attrs.update(
            {"id": "id_initial_garantieWR"}
        )
        # self.fields["initial_elwa"].widget.attrs.update({"id": "id_initial_elwa"})
        self.fields["initial_thor"].widget.attrs.update({"id": "id_initial_thor"})
        self.fields["initial_heizstab"].widget.attrs.update(
            {"id": "id_initial_heizstab"}
        )
        self.fields["initial_notstrom"].widget.attrs.update(
            {"id": "id_initial_notstrom"}
        )
        self.fields["initial_anzOptimizer"].widget.attrs.update(
            {"id": "id_initial_anzOptimizer"}
        )
        self.fields["initial_wallboxtyp"].widget.attrs.update(
            {"id": "id_initial_wallboxtyp"}
        )
        self.fields["initial_wallbox_anzahl"].widget.attrs.update(
            {"id": "id_initial_wallbox_anzahl"}
        )
        self.fields["initial_kabelanschluss"].widget.attrs.update(
            {"id": "id_initial_kabelanschluss"}
        )
        self.fields["initial_text_for_email"].widget.attrs.update(
            {"id": "id_initial_text_for_email"}
        )
        self.fields["smtp_body"].widget.attrs.update(
            {"id": "smtp_body"}
        )
        self.fields["top_verkaufer_container_view"].widget.attrs.update(
            {"id": "id_top_verkaufer_container_view"}
        )
        self.fields["profile_container_view"].widget.attrs.update(
            {"id": "id_profile_container_view"}
        )
        self.fields["activity_container_view"].widget.attrs.update(
            {"id": "id_activity_container_view"}
        )
        self.fields["angebot_statusubersicht_view"].widget.attrs.update(
            {"id": "id_angebot_statusubersicht_view"}
        )
        self.fields["pv_rechner_view"].widget.attrs.update({"id": "id_pv_rechner_view"})

        self.fields["records_fetch_limit"].widget.attrs.update(
            {"id": "id_records_fetch_limit"}
        )
        self.fields["anzahl_sol_module_view"].widget.attrs.update(
            {"id": "id_anzahl_sol_module_view"}
        )
