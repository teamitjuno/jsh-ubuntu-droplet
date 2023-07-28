from django import forms
from django.contrib.auth.forms import UserCreationForm

from django.core.exceptions import ValidationError
from authentication.models import User

from .models import (
    Position,
    ElectricInvoice,
    KundenData,
)

import re


def validate_name_surname(value):
    if not isinstance(value, str) or len(value.split()) < 2:
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Bitte geben Sie einen gültigen Namen und Nachnamen ein."
            ),
            params={"value": value},
        )

    if not re.match("^[A-Za-z\s]*$", value):  # type: ignore
        raise ValidationError(
            (
                "Ungültige Eingabe: %(value)s. Der Vor- und Nachname darf nur Buchstaben und Leerzeichen enthalten."
            ),
            params={"value": value},
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
                "Ungültige Eingabe: %(Wert)s. Eine gültige ganze Zahl größer oder gleich Null ist erforderlich."
            ),
            params={"value": value},
        )


abzweig_klemme_choices = [
    ("Hauptleitungsabzweigklemmen 35mm", "Hauptleitungsabzweigklemmen 35mm")
]

kabelkanal_choices = [
    ("Kabelschellen Metall", "Kabelschellen Metall"),
    ("Kabelkanal 10x60mm", "Kabelkanal 10x60mm"),
    ("Kabelkanal 30x30mm", "Kabelkanal 30x30mm"),
    ("Kabelkanal 60x60mm", "Kabelkanal 60x60mm"),
]
mantelleitung_choices = [
    ("Mantellleitung NYY-J 5x16qmm", "Mantellleitung NYY-J 5x16qmm"),
    ("Mantellleitung NYM-J 5x16qmm", "Mantellleitung NYM-J 5x16qmm"),
    ("Mantellleitung NYY-J 1x16qmm", "Mantellleitung NYY-J 1x16qmm"),
    ("Mantellleitung NYM-J 1x16qmm", "Mantellleitung NYM-J 1x16qmm"),
    ("Mantellleitung NYY-J 5x10qmm", "Mantellleitung NYY-J 5x10qmm"),
    ("Mantellleitung NYM-J 5x10qmm", "Mantellleitung NYM-J 5x10qmm"),
    ("Mantellleitung NYY-J 5x6qmm", "Mantellleitung NYY-J 5x6qmm"),
    ("Mantellleitung NYM-J 5x6qmm", "Mantellleitung NYM-J 5x6qmm"),
    ("Mantellleitung NYY-J 5x4qmm", "Mantellleitung NYY-J 5x4qmm"),
    ("Mantellleitung NYM-J 5x4qmm", "Mantellleitung NYM-J 5x4qmm"),
    ("Mantellleitung NYM-J 5x2.5qmm", "Mantellleitung NYM-J 5x2.5qmm"),
    ("Mantellleitung NYM-J 3x2.5qmm", "Mantellleitung NYM-J 3x2.5qmm"),
    ("Mantellleitung NYM-J 5x1.5qmm", "Mantellleitung NYM-J 5x1.5qmm"),
]
zahler_kabel_choices = [
    ("H07-VK 16mm² sw", "H07-VK 16mm² sw"),
    ("H07-VK 16mm² bl", "H07-VK 16mm² bl"),
    ("H07-VK 16mm² gn/ge", "H07-VK 16mm² gn/ge"),
    ("H07-VK 10mm² sw", "H07-VK 10mm² sw"),
    ("H07-VK 10mm² bl", "H07-VK 10mm² bl"),
    ("H07-VK 10mm² gn/ge", "H07-VK 10mm² gn/ge"),
    ("H07-VK 4mm² sw", "H07-VK 4mm² sw"),
    ("H07-VK 4mm² bl", "H07-VK 4mm² bl"),
    ("H07-VK 4mm² gn/ge", "H07-VK 4mm² gn/ge"),
    ("H07-VK 2.5mm² sw", "H07-VK 2.5mm² sw"),
    ("H07-VK 2.5mm² bl", "H07-VK 2.5mm² bl"),
    ("H07-VK 2.5mm² gn/ge", "H07-VK 2.5mm² gn/ge"),
]

leitungschutzschalter_choices = [
    (
        "Leitungsschutzschalter 3polig B16",
        "Leitungsschutzschalter 3polig B16",
    ),
    (
        "Leitungsschutzschalter 3polig B20",
        "Leitungsschutzschalter 3polig B20",
    ),
    (
        "Leitungsschutzschalter 3polig B25",
        "Leitungsschutzschalter 3polig B25",
    ),
    (
        "Leitungsschutzschalter 3polig B32",
        "Leitungsschutzschalter 3polig B32",
    ),
    (
        "Leitungsschutzschalter 3polig B40",
        "Leitungsschutzschalter 3polig B40",
    ),
    (
        "Leitungsschutzschalter 1polig B10",
        "Leitungsschutzschalter 1polig B10",
    ),
    (
        "Leitungsschutzschalter 1polig B16",
        "Leitungsschutzschalter 1polig B16",
    ),
    (
        "Leitungsschutzschalter 1polig B20",
        "Leitungsschutzschalter 1polig B20",
    ),
    (
        "Leitungsschutzschalter 1polig B25",
        "Leitungsschutzschalter 1polig B25",
    ),
]


sls_choices = [
    ("SLS  3polig E35A", "SLS  3polig E35A"),
    ("SLS  3polig E50A", "SLS  3polig E50A"),
    ("SLS  3polig E63A", "SLS  3polig E63A"),
]

uss_choices = [
    (
        "Überspannungsschutz (Kombiableiter Phasenschiene)",
        "Überspannungsschutz (Kombiableiter Phasenschiene)",
    ),
    (
        "Überspannungsschutz (Kombiableiter Hutschiene)",
        "Überspannungsschutz (Kombiableiter Hutschiene)",
    ),
]

b_material_choices = [
    ("Hauptschalter 3x63A", "Hauptschalter 3x63A"),
    (
        "Fehlerstromschutzschalter 4polig 40A/30mA",
        "Fehlerstromschutzschalter 4polig 40A/30mA",
    ),
    ("FI/LS 2polig 16A/30mA", "FI/LS 2polig 16A/30mA"),
    ("FI/LS 2polig 25A/30mA", "FI/LS 2polig 25A/30mA"),
    ("FI/LS 4polig 16A/30mA", "FI/LS 4polig 16A/30mA"),
    ("FI/LS 4polig 25A/30mA", "FI/LS 4polig 25A/30mA"),
    ("Kammschiene 3phasig", "Kammschiene 3phasig"),
    ("Kammschiene 3phasig (N)", "Kammschiene 3phasig (N)"),
    ("Phoenixkontakt-Klemmen PE/L/NT", "Phoenixkontakt-Klemmen PE/L/NT"),
    ("Phoenixkontakt-Klemmen L/L", "Phoenixkontakt-Klemmen L/L"),
    ("Phoenixkontakt-Einspeiseklemme N", "Phoenixkontakt-Einspeiseklemme N"),
    ("Kupferschiene N", "Kupferschiene N"),
    (
        "Phoenixkontakt-Einspeiseklemme N Seitendeckel",
        "Phoenixkontakt-Einspeiseklemme N Seitendeckel",
    ),
    ("Phoenixkontakt-Stufenklemmen", "Phoenixkontakt-Stufenklemmen"),
    (
        "Phoenixkontakt-Klemmen Seitendeckel grau",
        "Phoenixkontakt-Klemmen Seitendeckel grau",
    ),
    ("Endkappen Kammschiene", "Endkappen Kammschiene"),
    ("Berührungsschutz Kammschiene", "Berührungsschutz Kammschiene"),
    ("Klemmblock Hutschiene N", "Klemmblock Hutschiene N"),
    ("Klemmblock Hutschiene PE", "Klemmblock Hutschiene PE"),
    ("Installationsklemmen (-4mm²)", "Installationsklemmen (-4mm²)"),
    ("Installationsklemmen (-6mm²)", "Installationsklemmen (-6mm²)"),
    ("Installationsklemmen (-10mm²)", "Installationsklemmen (-10mm²)"),
    (
        "Hutschienenhalter Installationsklemmen",
        "Hutschienenhalter Installationsklemmen",
    ),
    ("Aufputz-Abzweigdosen", "Aufputz-Abzweigdosen"),
]

netz_typ_choices = [
    ("-TN-S-Netz", "-TN-S-Netz"),
    ("-TN-C-Netz", "-TN-C-Netz"),
    ("-TW-C-S-Netz", "-TW-C-S-Netz"),
    ("-TT-Netz", "-TT-Netz"),
]
zahlerschranken_choices = [
    ("1-Zähler-Anlagen", "1-Zähler-Anlagen"),
    ("2-Zähler-Anlagen", "2-Zähler-Anlagen"),
    ("3-Zähler-Anlagen", "3-Zähler-Anlagen"),
    ("4-Zähler-Anlagen", "4-Zähler-Anlagen"),
]

position_choices = []


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("id", "email", "username", "password1", "password2")


class ElectricInvoiceForm(forms.ModelForm):
    class Meta:
        model = ElectricInvoice
        fields = [
            "invoice_id",
            "is_locked",
        ]


class KundenDataForm(forms.ModelForm):
    class Meta:
        model = KundenData
        fields = [
            "kunden_name",
            "kunden_strasse",
            "kunden_plz_ort",
            "standort",
            "netz_typ",
            "zahlerschranken",
        ]

    kunden_name = forms.CharField(
        label="Vor- und Nachname",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Vor- und Nachname",
                "id": "kunden_name",
            }
        ),
    )
    kunden_strasse = forms.CharField(
        label="Straße",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Straße",
                "id": "kunden_strasse",
            }
        ),
    )
    kunden_plz_ort = forms.CharField(
        label="PLZ",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "PLZ",
                "id": "kunden_plz_ort",
            }
        ),
    )
    standort = forms.CharField(
        label="Stadt",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Stadt", "id": "standort"}
        ),
    )
    netz_typ = forms.ChoiceField(
        label="Netz´Typ",
        choices=netz_typ_choices,
        widget=forms.Select(attrs={"class": "form-select", "id": "netz_typ"}),
    )
    zahlerschranken = forms.ChoiceField(
        label="Anzahl Zählerfelder",
        choices=zahlerschranken_choices,
        widget=forms.Select(attrs={"id": "zahlerschranken", "class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super(KundenDataForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if self.initial.get(field):
                self.fields[field].widget.attrs.update(
                    {"placeholder": self.initial[field]}
                )

    def clean_kunden_name(self):
        cleaned_data = super().clean()
        kunden_name = cleaned_data.get("kunden_name")
        if not kunden_name:
            raise forms.ValidationError("Dieses Feld ist erforderlich.")
        return kunden_name

    def clean_kunden_strasse(self):
        cleaned_data = super().clean()
        kunden_strasse = cleaned_data.get("kunden_strasse")
        if not kunden_strasse:
            raise forms.ValidationError("Dieses Feld ist erforderlich.")
        return kunden_strasse

    def clean_kunden_plz_ort(self):
        cleaned_data = super().clean()
        kunden_plz_ort = cleaned_data.get("kunden_plz_ort")
        if not kunden_plz_ort:
            raise forms.ValidationError("Dieses Feld ist erforderlich.")
        return kunden_plz_ort

    def clean_standort(self):
        cleaned_data = super().clean()
        standort = cleaned_data.get("standort")
        if not standort:
            raise forms.ValidationError("Dieses Feld ist erforderlich.")
        return standort

    def save(self, *args, **kwargs):
        print("Saving KundenDataForm...")
        return super().save(*args, **kwargs)

    # widgets = {
    #     "kunden_name": forms.TextInput(
    #         attrs={"class": "mb-3", "placeholder": "Vor- und Nachname"}
    #     ),
    #     "kunden_strasse": forms.TextInput(
    #         attrs={"class": "mb-3", "placeholder": "Straße"}
    #     ),
    #     "kunden_plz_ort": forms.TextInput(
    #         attrs={"class": "form-control", "placeholder": "PLZ"}
    #     ),
    #     "standort": forms.TextInput(
    #         attrs={"class": "form-control", "placeholder": "Stadt"}
    #     ),
    #     "netz_typ": forms.Select(
    #         attrs={"class": "form-control", "placeholder": "Netz´Typ"}
    #     ),
    #     "zahlerschranken": forms.Select(
    #         attrs={"class": "form-control", "placeholder": "Anzahl Zählerfelder"}
    #     ),

    # }


class PositionForm(forms.ModelForm):
    position = forms.ChoiceField(
        choices=position_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "position"}),
    )
    quantity = forms.IntegerField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Menge"}),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class SlsForm(forms.ModelForm):
    sls = forms.ChoiceField(
        choices=sls_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "sls"}),
    )
    quantity = forms.IntegerField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Menge"}),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class UssForm(forms.ModelForm):
    uss = forms.ChoiceField(
        choices=uss_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "uss"}),
    )
    quantity = forms.IntegerField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Menge"}),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class BmaterialForm(forms.ModelForm):
    b_material = forms.ChoiceField(
        choices=b_material_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "b_material"}),
    )
    quantity = forms.IntegerField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Menge"}),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class LeitungschutzschalterForm(forms.ModelForm):
    leitungschutzschalter = forms.ChoiceField(
        choices=leitungschutzschalter_choices,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "leitungschutzschalter"}
        ),
    )
    quantity = forms.IntegerField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Menge", "id": "quantity"}
        ),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class HauptabzweigklemmeForm(forms.ModelForm):
    hauptabzweigklemme = forms.ChoiceField(
        choices=abzweig_klemme_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "hauptabzweigklemme"}),
    )
    quantity = forms.IntegerField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Menge", "id": "quantity"}
        ),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class MantelleitungForm(forms.ModelForm):
    mantelleitung = forms.ChoiceField(
        choices=mantelleitung_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "mantelleitung"}),
    )
    quantity = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Menge"}
        ),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class KabelKanalForm(forms.ModelForm):
    kabelkanal = forms.ChoiceField(
        choices=kabelkanal_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "kabelkanal"}),
    )
    quantity = forms.FloatField(
        required=False,
        validators=[validate_floats],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Menge"}
        ),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


class ZahlerKabelForm(forms.ModelForm):
    zahler_kabel = forms.ChoiceField(
        choices=zahler_kabel_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "zahler_kabel"}),
    )
    quantity = forms.FloatField(
        required=False,
        validators=[validate_floats],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Menge"}
        ),
    )

    class Meta:
        model = Position
        fields = ["position", "quantity"]


from django import forms


class UploadXlsxForm(forms.Form):
    file1 = forms.FileField(widget=forms.FileInput(
            attrs={"class": "fallback",  "id" : "myAwesomeDropzone"}
        ),)
