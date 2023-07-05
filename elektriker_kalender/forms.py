from django import forms
from django.core.exceptions import ValidationError
from .models import ElectricCalendar, Position, PVAKlein1

POSITION_CHOICES = [
    ("Hauptleitungsabzweigklemmen 35mm", "Hauptleitungsabzweigklemmen 35mm"),
    ("Kabelschellen Metall", "Kabelschellen Metall"),
    ("Kabelkanal 10x60mm", "Kabelkanal 10x60mm"),
    ("Kabelkanal 30x30mm", "Kabelkanal 30x30mm"),
    ("Kabelkanal 60x60mm", "Kabelkanal 60x60mm"),
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
    (
        "Leitungsschutzschalter 3polig B16 leGrand",
        "Leitungsschutzschalter 3polig B16 leGrand",
    ),
    (
        "Leitungsschutzschalter 3polig B20 leGrand",
        "Leitungsschutzschalter 3polig B20 leGrand",
    ),
    (
        "Leitungsschutzschalter 3polig B25 leGrand",
        "Leitungsschutzschalter 3polig B25 leGrand",
    ),
    (
        "Leitungsschutzschalter 3polig B32 leGrand",
        "Leitungsschutzschalter 3polig B32 leGrand",
    ),
    (
        "Leitungsschutzschalter 3polig B40 leGrand",
        "Leitungsschutzschalter 3polig B40 leGrand",
    ),
    (
        "Leitungsschutzschalter 1polig B10 leGrand",
        "Leitungsschutzschalter 1polig B10 leGrand",
    ),
    (
        "Leitungsschutzschalter 1polig B16 leGrand",
        "Leitungsschutzschalter 1polig B16 leGrand",
    ),
    (
        "Leitungsschutzschalter 1polig B20 leGrand",
        "Leitungsschutzschalter 1polig B20 leGrand",
    ),
    (
        "Leitungsschutzschalter 1polig B25 leGrand",
        "Leitungsschutzschalter 1polig B25 leGrand",
    ),
    ("SLS  3polig E35A", "SLS  3polig E35A"),
    ("SLS  3polig E50A", "SLS  3polig E50A"),
    ("SLS  3polig E63A", "SLS  3polig E63A"),
    (
        "Uberspannungsschutz (Kombiableiter Phasenschiene DEHN)",
        "Uberspannungsschutz (Kombiableiter Phasenschiene DEHN)",
    ),
    (
        "Uberspannungsschutz (Kombiableiter Hutschiene DEHN)",
        "Uberspannungsschutz (Kombiableiter Hutschiene DEHN)",
    ),
    ("Hauptschalter 3x63A", "Hauptschalter 3x63A"),
    (
        "Fehlerstromschutzschalter 4polig 40A/30mA",
        "Fehlerstromschutzschalter 4polig 40A/30mA",
    ),
    ("FI/LS 2polig 16A/30mA", "FI/LS 2polig 16A/30mA"),
    ("FI/LS 2polig 25A/30mA", "FI/LS 2polig 25A/30mA"),
    ("FI/LS 4polig 16A/30mA", "FI/LS 4polig 16A/30mA"),
    ("FI/LS 4polig 25A/30mA", "FI/LS 4polig 25A/30mA"),
    ("Kammschiene 3phasig HAGER", "Kammschiene 3phasig HAGER"),
    ("Kammschiene 3phasig HAGER (N)", "Kammschiene 3phasig HAGER (N)"),
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
    ("WAGO-Klemmen (-4mm²)", "WAGO-Klemmen (-4mm²)"),
    ("WAGO-Klemmen (-6mm²)", "WAGO-Klemmen (-6mm²)"),
    ("WAGO-Klemmen (-10mm²)", "WAGO-Klemmen (-10mm²)"),
    ("Hutschienenhalter WAGO-Klemmen", "Hutschienenhalter WAGO-Klemmen"),
    ("Aufputz-Abzweigdosen", "Aufputz-Abzweigdosen"),
]


class ElectricCalendarForm(forms.ModelForm):
    class Meta:
        model = ElectricCalendar
        fields = [
            "calendar_id",
            "zoho_id",
            "user",
            "anschluss_PVA",
            "elektriker_calfield",
            "kundenname",
            "pva_klein1_calfield",
            "privatkunde_adresse_pva",
            "besonderheiten",
            "elektriktermin_am",
            "kundenname_rawdata",
            "termin_best_tigt",
        ]
        widgets = {
            "anschluss_PVA": forms.TextInput(attrs={"class": "form-control"}),
            "kundenname": forms.TextInput(attrs={"class": "form-control"}),
            "privatkunde_adresse_pva": forms.TextInput(attrs={"class": "form-control"}),
            "besonderheiten": forms.Textarea(attrs={"class": "form-control"}),
            "elektriktermin_am": forms.DateTimeInput(attrs={"class": "form-control"}),
            "kundenname_rawdata": forms.TextInput(attrs={"class": "form-control"}),
            "termin_best_tigt": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # place for custom validations here

        return cleaned_data


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ["position", "quantity"]
        widgets = {
            "position": forms.Select(
                choices=POSITION_CHOICES, attrs={"class": "form-control"}
            ),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # place for custom validations here

        return cleaned_data


class PVAKlein1Form(forms.ModelForm):
    class Meta:
        model = PVAKlein1
        fields = ["display_value", "calendar"]
        widgets = {
            "display_value": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # place for custom validations here

        return cleaned_data


# class KundenDataForm(forms.ModelForm):
#     class Meta:
#         model = KundenData
#         fields = [
#             "kunden_name",
#             "kunden_strasse",
#             "kunden_plz_ort",
#             "standort",
#             "calendar",
#         ]

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields["kunden_name"].widget = forms.TextInput(
#             attrs={"placeholder": "Enter Kunden Name", "class": "form-control"}
#         )
#         self.fields["kunden_strasse"].widget = forms.TextInput(
#             attrs={"placeholder": "Enter Kunden Strasse", "class": "form-control"}
#         )
#         self.fields["kunden_plz_ort"].widget = forms.TextInput(
#             attrs={"placeholder": "Enter Kunden PLZ Ort", "class": "form-control"}
#         )
#         self.fields["standort"].widget = forms.TextInput(
#             attrs={"placeholder": "Enter Standort", "class": "form-control"}
#         )
#         self.fields["calendar"].widget = forms.Select(attrs={"class": "form-control"})


# class PositionForm(forms.ModelForm):


# position = forms.ChoiceField(choices=POSITION_CHOICES)

# class Meta:
#     model = Position
#     fields = ["position", "quantity", "kunde"]

# def __init__(self, *args, **kwargs):
#     super().__init__(*args, **kwargs)
#     self.fields["position"].widget = forms.Select(attrs={"class": "form-control"})
#     self.fields["quantity"].widget = forms.NumberInput(
#         attrs={"placeholder": "Enter Quantity", "class": "form-control"}
#     )
#     self.fields["kunde"].widget = forms.Select(attrs={"class": "form-control"})
