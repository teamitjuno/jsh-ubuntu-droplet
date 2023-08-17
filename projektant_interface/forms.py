from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):

    Status = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Status",
                "id": "id_Status",
            }
        ),
        required=False,
    )

    Auftragsbest_tigung_versendet = forms.ChoiceField(
        choices=[('Ja', 'Ja'), ('Nein', 'Nein')],
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_Auftragsbest_tigung_versendet",
            }
        ),
        required=False,
    )

    Auftrag_Erteilt_am = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "id": "id_Auftrag_Erteilt_am",
            }
        ),
        required=False,
    )

    Kunde_display_value = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kunde Display Value",
                "id": "id_Kunde_display_value",
            }
        ),
        required=False,
    )
    Modul_Summe_kWp = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Modul Summe kWp",
                "id": "id_Modul_Summe_kWp",
            }
        ),
        required=False,
    )

    Besonderheiten = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Besonderheiten",
                "id": "id_Besonderheiten",
            }
        ),
        required=False,
    )

    Rechnung_versandt = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Rechnung versandt",
                "id": "id_Rechnung_versandt",
            }
        ),
        required=False,
    )

    UK_vsl_Lieferung = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "UK vsl Lieferung",
                "id": "id_UK_vsl_Lieferung",
            }
        ),
        required=False,
    )
    Berechnung_erhalten_am = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Berechnung erhalten am",
                "id": "id_Berechnung_erhalten_am",
            }
        ),
        required=False,
    )

    EDDI = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_EDDI",
            }
        ),
        required=False,
    )

    Netzbetreiber = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Netzbetreiber",
                "id": "id_Netzbetreiber",
            }
        ),
        required=False,
    )
    Garantie_WR_beantragt_am = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Garantie WR beantragt am",
                "id": "id_Garantie_WR_beantragt_am",
            }
        ),
        required=False,
    )

    Ticket_form = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ticket form",
                "id": "id_Ticket_form",
            }
        ),
        required=False,
    )

    Status_Inbetriebnahmeprotokoll = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Status Inbetriebnahmeprotokoll",
                "id": "id_Status_Inbetriebnahmeprotokoll",
            }
        ),
        required=False,
    )

    Zahlungsmodalit_ten = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Zahlungsmodalitäten",
                "id": "id_Zahlungsmodalit_ten",
            }
        ),
        required=False,
    )
    Vertriebler = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Vertriebler",
                "id": "id_Vertriebler",
            }
        ),
        required=False,
    )

    Notstromversorgung_Backup_Box_vorhanden = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_Notstromversorgung_Backup_Box_vorhanden",
            }
        ),
        required=False,
    )

    Status_Marktstammdatenregistrierung = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Status Marktstammdatenregistrierung",
                "id": "id_Status_Marktstammdatenregistrierung",
            }
        ),
        required=False,
    )

    Garantieerweiterung = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Garantieerweiterung",
                "id": "id_Garantieerweiterung",
            }
        ),
        required=False,
    )

    Bauabschluss_am = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Bauabschluss am",
                "id": "id_Bauabschluss_am",
            }
        ),
        required=False,
    )

    Status_Betreiberwechsel = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Status Betreiberwechsel",
                "id": "id_Status_Betreiberwechsel",
            }
        ),
        required=False,
    )

    Status_Einspeiseanfrage = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Status Einspeiseanfrage",
                "id": "id_Status_Einspeiseanfrage",
            }
        ),
        required=False,
    )

    Hub1 = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_Hub1",
            }
        ),
        required=False,
    )

    Kunde_Kundennummer = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kunde Kundennummer",
                "id": "id_Kunde_Kundennummer",
            }
        ),
        required=False,
    )

    UK_auf_Lager = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_UK_auf_Lager",
            }
        ),
        required=False,
    )

    UK_bestellt_am = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "UK bestellt am",
                "id": "id_UK_bestellt_am",
            }
        ),
        required=False,
    )

    Power_Boost_vorhanden = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_Power_Boost_vorhanden",
            }
        ),
        required=False,
    )

    Unterkonstruktion1 = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Unterkonstruktion1",
                "id": "id_Unterkonstruktion1",
            }
        ),
        required=False,
    )

    Harvi1 = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Harvi1",
                "id": "id_Harvi1",
            }
        ),
        required=False,
    )

    Optimizer1 = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Optimizer1",
                "id": "id_Optimizer1",
            }
        ),
        required=False,
    )

    Kunde_Adresse_PVA = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kunde Adresse PVA",
                "id": "id_Kunde_Adresse_PVA",
            }
        ),
        required=False,
    )

    Status_Elektrik = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Status Elektrik",
                "id": "id_Status_Elektrik",
            }
        ),
        required=False,
    )

    Kunde_Email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kunde Email",
                "id": "id_Kunde_Email",
            }
        ),
        required=False,
    )

    Termin_Z_hlerwechsel = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Termin Zählerwechsel",
                "id": "id_Termin_Z_hlerwechsel",
            }
        ),
        required=False,
    )

    Nummer_der_PVA = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nummer der PVA",
                "id": "id_Nummer_der_PVA",
            }
        ),
        required=False,
    )

    Kunde_Postanschrift = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kunde Postanschrift",
                "id": "id_Kunde_Postanschrift",
            }
        ),
        required=False,
    )

    Kunde_Telefon_Festnetz = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kunde Telefon Festnetz",
                "id": "id_Kunde_Telefon_Festnetz",
            }
        ),
        required=False,
    )
    Kunde_Telefon_mobil = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Kunde Telefon mobil",
                "id": "id_Kunde_Telefon_mobil",
            }
        ),
        required=False,
    )

    Status_Fertigmeldung = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Status Fertigmeldung",
                "id": "id_Status_Fertigmeldung",
            }
        ),
        required=False,
    )

    Bauleiter = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Bauleiter",
                "id": "id_Bauleiter",
            }
        ),
        required=False,
    )

    Hauselektrik = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Hauselektrik",
                "id": "id_Hauselektrik",
            }
        ),
        required=False,
    )

    class Meta:
        model = Project
        fields = "__all__"