import datetime
from django.db import models
from django.contrib.auth import get_user_model
from shared.models import TimeStampMixin

position_choices = [
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
    ("SLS  3polig E35A", "SLS  3polig E35A"),
    ("SLS  3polig E50A", "SLS  3polig E50A"),
    ("SLS  3polig E63A", "SLS  3polig E63A"),
    (
        "Überspannungsschutz (Kombiableiter Phasenschiene)",
        "Überspannungsschutz (Kombiableiter Phasenschiene)",
    ),
    (
        "Überspannungsschutz (Kombiableiter Hutschiene)",
        "Überspannungsschutz (Kombiableiter Hutschiene)",
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
zahlerschrank_model_choices = [("Model1", "Model1"), ("Model2", "Model2")]

User = get_user_model()


class ElectricInvoice(TimeStampMixin):
    invoice_id = models.CharField(max_length=255, unique=True, default=None)
    current_date = models.DateField(auto_now_add=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_locked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.invoice_id = self.generate_invoice_id()
            self.is_locked = False

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"InvoiceID: {self.invoice_id}"

    def generate_invoice_id(self):
        user = User.objects.get(id=self.user.pk)
        kurz = user.kuerzel  # type: ignore
        current_datetime = datetime.datetime.now()
        return f"AN-{kurz}{current_datetime.strftime('%d%m%Y-%H%M%S')}"


class KundenData(TimeStampMixin):
    kunden_name = models.CharField(max_length=100, blank=True, null=True)
    kunden_strasse = models.CharField(max_length=100, blank=True, null=True)
    kunden_plz_ort = models.CharField(max_length=100, blank=True, null=True)
    standort = models.CharField(max_length=100, blank=True, null=True)
    zahlerschranken = models.CharField(
        max_length=100, choices=zahlerschranken_choices, blank=False
    )
    # zahlerschrank_model = models.CharField(
    #     max_length=100, choices=zahlerschrank_model_choices, blank=False
    # )
    netz_typ = models.CharField(max_length=100, choices=netz_typ_choices, blank=False)
    invoice = models.OneToOneField(
        ElectricInvoice,
        on_delete=models.CASCADE,
        related_name="kunden_data",
    )

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class Position(TimeStampMixin):
    position = models.CharField(
        max_length=100, choices=position_choices, blank=True, null=True
    )
    quantity = models.FloatField(null=True, blank=True)
    invoice = models.ForeignKey(
        "ElectricInvoice",
        on_delete=models.CASCADE,
        related_name="positions",
    )

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.position}, Menge : {self.quantity}"
