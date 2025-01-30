from django import forms
from .models import Calculator
from prices.models import SolarModulePreise, WallBoxPreise
from django.core.exceptions import ValidationError
import decimal


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
    if value < 6 and value != 0:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Die Anzahl der Solarmodule sollte 6 oder mehr betragen."
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


class CalculatorForm(forms.ModelForm):
    solar_module = forms.ChoiceField(
        label="Solar Module",
        widget=forms.Select(attrs={"class": "form-select", "id": "solar_module"}),
    )

    modulanzahl = forms.IntegerField(
        label="Module Anzahl",
        initial=0,
        validators=[validate_solar_module_anzahl],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_modulanzahl",
            }
        ),
    )
    wallboxtyp = forms.ChoiceField(
        required=False,
        label="Wallbox",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "wallboxtyp",
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
                "id": "id_wallbox_anzahl",
            }
        ),
    )
    optimizer = forms.BooleanField(
        label="Optimizer",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input form-check-input mb-3", "id": "optimizer"}
        ),
    )
    notstrom = forms.BooleanField(
        label="Notstrom",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input form-check-input mb-3", "id": "notstrom"}
        ),
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
    heizstab = forms.BooleanField(
        label="Heizstab inklusive",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "heizstab-checkbox",
                "style": "max-width: 300px",
            }
        ),
    )
    anzOptimizer = forms.IntegerField(
        label="Optimizer",
        required=True,
        validators=[validate_integers],
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control mb-3", "id": "id_anzOptimizer"}
        ),
    )
    anz_speicher = forms.IntegerField(
        label="Speichermodule Anzahl (kann 0 sein)",
        required=False,
        initial=0,
        validators=[validate_range],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control form-control mb-3",
                "id": "id_anz_speicher",
            }
        ),
    )
    speicher = forms.BooleanField(
        label="Speichermodule",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input form-check-input mb-3",
                "id": "speicher",
            }
        ),
    )
    angebotsumme = forms.FloatField(
        label="Angebotsumme: ",
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "badge badge-info-lighten", "id": "id_angebotsumme"}
        ),
    )

    def __init__(self, *args, user, **kwargs):
        super(CalculatorForm, self).__init__(*args, **kwargs)

        self.fields["solar_module"].choices = [
            (module.name, module.name)
            for module in SolarModulePreise.objects.filter(in_stock=True)
        ]
        self.fields["wallboxtyp"].choices = [
            (module.name, module.name)
            for module in WallBoxPreise.objects.filter(in_stock=True)
        ]
        self.fields["wallbox_anzahl"].widget.attrs.update({"id": "wallbox_anzahl"})
        self.fields["modulanzahl"].widget.attrs.update({"id": "modulanzahl"})
        self.fields["anzOptimizer"].widget.attrs.update({"id": "anzOptimizer"})
        self.fields["anz_speicher"].widget.attrs.update({"id": "anz_speicher"})
        self.fields["angebotsumme"].widget.attrs.update({"id": "angebotsumme"})

        for field in self.fields:
            if self.initial.get(field):
                self.fields[field].widget.attrs.update(
                    {"placeholder": self.initial[field]}
                )

    def save(self, commit=True):
        calculator_form = super(CalculatorForm, self).save(commit=False)

        if commit:
            calculator_form.save()

        return calculator_form

    class Meta:
        model = Calculator
        fields = [
            "solar_module",
            "modulanzahl",
            "notstrom",
            "elwa",
            "thor",
            "heizstab",
            "optimizer",
            "anzOptimizer",
            "wallboxtyp",
            "wallbox_anzahl",
            "speicher",
            "anz_speicher",
            "angebotsumme",
        ]
