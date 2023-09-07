from django.db import models
import datetime
import re


class Elektriktermin(models.Model):
    display_value = models.CharField(max_length=255)
    ID = models.CharField(max_length=50, unique=True)


class Bautermine(models.Model):
    display_value = models.CharField(max_length=255)
    ID = models.CharField(max_length=50, unique=True)


class Module1(models.Model):
    display_value = models.CharField(max_length=255)
    ID = models.CharField(max_length=50, unique=True)


class Wallbox1(models.Model):
    display_value = models.CharField(max_length=255)
    ID = models.CharField(max_length=50, unique=True)


class Wechselrichter1(models.Model):
    display_value = models.CharField(max_length=255)
    ID = models.CharField(max_length=50, unique=True)


class Speicher(models.Model):
    display_value = models.CharField(max_length=255)
    ID = models.CharField(max_length=50, unique=True)


class Project(models.Model):
    ID = models.CharField(max_length=50, primary_key=True)
    Status = models.CharField(max_length=255)

    Auftragsbest_tigung_versendet = models.CharField(max_length=5)
    Auftrag_Erteilt_am = models.DateField(null=True, blank=True)
    Kunde_display_value = models.CharField(max_length=255)
    Kunde_ID = models.CharField(max_length=50, unique=False)
    Bautermine = models.CharField(max_length=255, null=True, blank=True)
    Modul_Summe_kWp = models.CharField(max_length=255, blank=True)
    Module1 = models.CharField(max_length=255, null=True, blank=True)
    Besonderheiten = models.TextField()  # Rich text representation
    Processed_Besonderheiten = models.TextField(default="keine Beschreibung")
    Elektriktermin = models.CharField(max_length=255, null=True, blank=True)
    Rechnung_versandt = models.CharField(max_length=255, blank=True)

    Lieferung = models.DateField(null=True, blank=True)

    Berechnung_erhalten_am = models.CharField(max_length=255, blank=True, null=True)
    EDDI = models.BooleanField(default=False)
    Netzbetreiber = models.CharField(max_length=255, blank=True, null=True)
    Garantie_WR_beantragt_am = models.CharField(max_length=255, blank=True, null=True)
    Ticket_form = models.CharField(max_length=255, blank=True, null=True)
    Status_Inbetriebnahmeprotokoll = models.CharField(
        max_length=255, blank=True, null=True
    )
    Zahlungsmodalit_ten = models.CharField(max_length=255, blank=True, null=True)
    Berechnung_bergeben_am = models.CharField(max_length=255, blank=True, null=True)
    Vertriebler = models.CharField(max_length=255, blank=True, null=True)
    Notstromversorgung_Backup_Box_vorhanden = models.BooleanField(default=False)
    Status_Marktstammdatenregistrierung = models.CharField(
        max_length=255, blank=True, null=True
    )
    Garantieerweiterung = models.CharField(max_length=255, blank=True, null=True)
    Bauabschluss_am = models.CharField(max_length=255, blank=True, null=True)
    Status_Betreiberwechsel = models.CharField(max_length=255, blank=True, null=True)
    Status_Einspeiseanfrage = models.CharField(max_length=255, blank=True, null=True)
    Wallbox1 = models.CharField(max_length=255, null=True, blank=True)
    Hub1 = models.BooleanField(default=False)
    Kunde_Kundennummer = models.CharField(max_length=255, blank=True, null=True)
    UK_auf_Lager = models.BooleanField(default=False)
    Wechselrichter1 = models.TextField(null=True, blank=True)
    UK_bestellt_am = models.CharField(max_length=255, blank=True, null=True)
    Power_Boost_vorhanden = models.BooleanField(default=False)
    Unterkonstruktion1 = models.CharField(max_length=255, blank=True, null=True)
    Harvi1 = models.CharField(max_length=255, blank=True, null=True)
    Optimizer1 = models.CharField(max_length=255, blank=True, null=True)
    Kunde_Adresse_PVA = models.CharField(max_length=255, blank=True, null=True)
    Status_Elektrik = models.CharField(max_length=255, blank=True, null=True)
    Kunde_Email = models.CharField(max_length=255, blank=True, null=True)
    Termin_Z_hlerwechsel = models.CharField(max_length=255, blank=True, null=True)
    Nummer_der_PVA = models.CharField(max_length=255, blank=True, null=True)
    Kunde_Postanschrift = models.CharField(max_length=255, blank=True, null=True)
    Kunde_Telefon_Festnetz = models.CharField(max_length=255, blank=True, null=True)
    Speicher = models.CharField(max_length=255, null=True, blank=True)
    Status_Fertigmeldung = models.CharField(max_length=255, blank=True, null=True)
    Bauleiter = models.CharField(max_length=255, blank=True, null=True)
    Hauselektrik = models.CharField(max_length=255, blank=True, null=True)
    Kunde_Telefon_mobil = models.CharField(max_length=255, blank=True, null=True)

    temp_content_pdf = models.BinaryField(blank=True, null=True)
    bauplan_pdf = models.BinaryField(blank=True, null=True)
    bauplan_img = models.ImageField(upload_to="assets/images/layouts/", null=True, blank=True)
    bauplan_img_secondary = models.ImageField(upload_to="assets/images/layouts/", null=True, blank=True)
    bauplan_img_third = models.ImageField(upload_to="assets/images/layouts/", null=True, blank=True)
    font_size = models.PositiveIntegerField(default=18, blank=True, null=True)
    email_form = models.CharField(max_length=255, blank=True, null=True)

    roof_typ = models.CharField(max_length=255, blank=True, null=True)
    height = models.CharField(max_length=255, blank=True, null=True)
    current_date = models.DateField(auto_now_add=True, null=True, blank=True)

    kunden_name = models.CharField(max_length=255, blank=True, null=True)
    solar_module = models.CharField(max_length=255, blank=True, null=True)
    ticket_id = models.CharField(max_length=255, blank=True, null=True)
    vertriebler = models.CharField(max_length=255, blank=True, null=True)
    wallbox = models.CharField(max_length=255, blank=True, null=True)
    wechselrichter = models.CharField(max_length=255, blank=True, null=True)
    unterkonstrution = models.CharField(max_length=255, blank=True, null=True)
    speicher = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.kunden_name = self.kunde_display_value
        self.solar_module = self.solar_module_display_value
        self.ticket_id = self.ticket_id_display_value
        self.vertriebler = self.vertribler_display_value
        self.wallbox = self.wallbox_display_value
        self.wechselrichter = self.wechselrichter_display_value
        self.unterkonstrution = self.unterkonstruktion_display_value
        self.speicher = self.speicher_display_value
        super().save(*args, **kwargs)

    @property
    def kunde_display_value(self):
        if self.Kunde_display_value is not None:
            data_str = self.Kunde_display_value
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"

    @property
    def solar_module_display_value(self):
        if self.Module1 is not None:
            data_str = str(self.Module1)
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"

    @property
    def ticket_id_display_value(self):
        if self.Ticket_form is not None and self.Ticket_form != "":
            data_str = str(self.Ticket_form)
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"

    @property
    def vertribler_display_value(self):
        if self.Vertriebler is not None and self.Vertriebler != "":
            data_str = str(self.Kunde_display_value)
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"

    @property
    def wallbox_display_value(self):
        if self.Wallbox1 is not None and self.Wallbox1 != []:
            data_str = str(self.Wallbox1)
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"

    @property
    def wechselrichter_display_value(self):
        if self.Wechselrichter1 is not None and self.Wechselrichter1 != []:
            data_str = str(self.Wechselrichter1)
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"

    @property
    def unterkonstruktion_display_value(self):
        if self.Unterkonstruktion1 is not None and self.Unterkonstruktion1 != []:
            data_str = str(self.Unterkonstruktion1)
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"

    @property
    def speicher_display_value(self):
        if self.Speicher is not None and self.Speicher != []:
            data_str = str(self.Speicher)
            match = re.search(r"'display_value':\s*'([^']+)'", data_str)
            return match.group(1).strip() if match else None
        else:
            return "keine"
