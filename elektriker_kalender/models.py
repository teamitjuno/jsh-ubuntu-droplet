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

User = get_user_model()


class ElectricCalendar(TimeStampMixin):
    calendar_id = models.CharField(
        max_length=255, primary_key=True, unique=True, default=None
    )
    zoho_id = models.CharField(max_length=20, default="")
    current_date = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_locked = models.BooleanField(default=False)

    anschluss_PVA = models.CharField(max_length=50, null=True, blank=True)
    elektriker_calfield = models.BigIntegerField(null=True, blank=True)
    kundenname = models.CharField(max_length=255, null=True, blank=True)
    pva_klein1_calfield = models.BigIntegerField(null=True, blank=True)
    privatkunde_adresse_pva = models.CharField(max_length=255, null=True, blank=True)
    besonderheiten = models.TextField(default="Besonderheiten", null=True, blank=True)
    elektriktermin_am = models.DateTimeField(null=True, blank=True)
    kundenname_rawdata = models.CharField(max_length=255, null=True, blank=True)
    termin_best_tigt = models.CharField(max_length=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.calendar_id = self.generate_calendar_id()
            self.is_locked = False

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"CalendarID: {self.calendar_id}"

    def generate_calendar_id(self):
        user = User.objects.get(id=self.user.pk)
        kurz = user.kuerzel  # type: ignore
        current_datetime = datetime.datetime.now()
        return f"CAL-{kurz}-{current_datetime.strftime('%d%m%Y-%H%M%S')}"


class Position(TimeStampMixin):
    position = models.CharField(
        max_length=100, choices=position_choices, blank=True, null=True
    )
    quantity = models.FloatField(null=True, blank=True)
    calendar = models.ForeignKey(
        "ElectricCalendar",
        on_delete=models.CASCADE,
        related_name="positions",
        default=ElectricCalendar,
    )

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.position}, Menge : {self.quantity}"


class PVAKlein1(models.Model):
    display_value = models.CharField(max_length=255)
    pva_id = models.CharField(max_length=20)
    calendar = models.ForeignKey(
        "ElectricCalendar",
        on_delete=models.CASCADE,
        related_name="pva_kleins1",
    )

    def __str__(self):
        return self.display_value
