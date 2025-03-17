from django.db import models
from authentication.models import User
from django.core.validators import MinValueValidator
from prices.models import (
    WrGarantiePreise,
    KwpPreise,
    OptionalAccessoriesPreise,
    AndereKonfigurationWerte,
    SolarModulePreise,
    WallBoxPreise,
)
from math import ceil
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils.formats import date_format

now = timezone.now()
now_german = date_format(now, "DATETIME_FORMAT")


def get_price(model, name):
    model_name = model.__name__
    key = f"{model_name}_{name}"
    price = cache.get(key)
    if price is None:
        try:
            price = model.objects.get(name=name).price
        except ObjectDoesNotExist:
            price = 0
        cache.set(key, price)
    return price


# Model properties
MODULE_NAME_MAP = {
    "Phono Solar PS420M7GFH-18/VNH": "Phono Solar PS420M7GFH-18/VNH",
    "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B": "Jinko Solar Tiger Neo N-type JKM425N-54HL4-B",
}
ACCESSORY_NAME = "leistungsmodul"
BATT_DICT = {1: 0.6, 2: 0.7, 3: 0.75, 4: 0.8, 5: 0.85, 6: 0.92}
DEFAULT_BATT_USAGE = 0.3


class Calculator(models.Model):
    calculator_id = models.CharField(max_length=255, unique=True, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    AUSRICHTUNG_CHOICES = (
        ("Sud", "Sud"),
        ("Ost/West", "Ost/West"),
    )
    KOMPLEX_CHOICES = (
        ("einfach, einfach erreichbar", "einfach, einfach erreichbar"),
        ("einfach, schwer erreichbar", "einfach, schwer erreichbar"),
        ("komplex, einfach erreichbar", "komplex, einfach erreichbar"),
        ("komplex, schwer erreichbar", "komplex, schwer erreichbar"),
        ("sehr komplex", "sehr komplex"),
    )

    verbrauch = models.FloatField(
        default=15000, validators=[MinValueValidator(0)]  # type: ignore
    )
    grundpreis = models.FloatField(
        default=9.8, validators=[MinValueValidator(0)]  # type: ignore
    )
    arbeitspreis = models.FloatField(
        default=46.8, validators=[MinValueValidator(0)]  # type: ignore
    )
    prognose = models.FloatField(
        default=5.2, validators=[MinValueValidator(0)]  # type: ignore
    )
    zeitraum = models.PositiveIntegerField(default=15)
    bis10kWp = models.FloatField(
        default=8.20, validators=[MinValueValidator(0)]  # type: ignore
    )
    bis40kWp = models.FloatField(
        default=7.10, validators=[MinValueValidator(0)]  # type: ignore
    )
    speicher = models.BooleanField(default=False)
    anz_speicher = models.PositiveIntegerField(default=0)
    speicher_model = models.CharField(
        max_length=100,
        default="LUNA 2000-7-S1",
    )
    wallbox = models.BooleanField(default=False)
    ausrichtung = models.CharField(
        max_length=10, choices=AUSRICHTUNG_CHOICES, default="Ost/West"
    )
    komplex = models.CharField(
        max_length=30, choices=KOMPLEX_CHOICES, default="sehr komplex"
    )

    GARANTIE_WR_CHOICES = [
        ("keine", "keine"),
        ("15 Jahre", "15 Jahre"),
    ]
    solar_module = models.CharField(
        max_length=100,
        default="Phono Solar PS420M7GFH-18/VNH",
    )
    modulleistungWp = models.PositiveIntegerField(default=420)
    modulanzahl = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    garantieWR = models.CharField(
        max_length=10, choices=GARANTIE_WR_CHOICES, default="keine"
    )
    elwa = models.BooleanField(default=False)
    thor = models.BooleanField(default=False)
    heizstab = models.BooleanField(default=False)
    notstrom = models.BooleanField(default=False)
    optimizer = models.BooleanField(default=False)
    anzOptimizer = models.PositiveIntegerField(default=0)

    wallboxtyp = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    wallbox_anzahl = models.PositiveIntegerField(default=0)
    kabelanschluss = models.FloatField(default=10.0, validators=[MinValueValidator(0)])
    hub_included = models.BooleanField(default=False)

    solar_module_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    batteriespeicher_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    wallbox_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    notstrom_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    optimizer_angebot_price = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    angebotsumme = models.FloatField(default=0.00, validators=[MinValueValidator(0)])

    benotigte_restenergie = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    nutzbare_nutzenergie = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    erzeugte_energie_pro_jahr = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    einspreisevergütung_gesamt = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )
    abzug_vergutung = models.FloatField(default=0.00, validators=[MinValueValidator(0)])
    Ersparnis = models.FloatField(default=0.00)
    kosten_fur_restenergie = models.FloatField(
        default=0.00, validators=[MinValueValidator(0)]
    )

    Rest_liste = models.TextField(blank=True, null=True)
    Arbeits_liste = models.TextField(blank=True, null=True)
    Full_ticket_preis = models.FloatField(default=0.00)

    def get_optional_accessory_price(self, name):
        return float(OptionalAccessoriesPreise.objects.get(name=name).price)

    def get_module_preis(self, name):
        return float(SolarModulePreise.objects.get(name=name).price)

    def get_wr_garantie_preis(self, name):
        return float(WrGarantiePreise.objects.get(name=name).price)

    def get_leistungs_garantie(self, name):
        return str(SolarModulePreise.objects.get(name=name).leistungs_garantie)

    def save(self, *args, **kwargs):
        self.wallbox_angebot_price = self.full_wallbox_preis
        self.notstrom_angebot_price = self.get_optional_accessory_price("backup_box")
        self.optimizer_angebot_price = float(self.full_optimizer_preis)
        if self.batteriespeicher_preis:
            self.batteriespeicher_angebot_price = self.batteriespeicher_preis
        self.angebotsumme = round(self.angebots_summe, 2)
        self.benotigte_restenergie = self.restenergie
        self.nutzbare_nutzenergie = self.nutz_energie
        self.erzeugte_energie_pro_jahr = self.erzeugte_energie
        self.einspreisevergütung_gesamt = self.einsp_verg
        self.abzug_vergutung = self.abzug
        self.Ersparnis = self.ersparnis
        self.kosten_fur_restenergie = self.kosten_rest_energie
        self.Rest_liste = self.rest_liste
        self.Arbeits_liste = self.arbeits_liste

        super().save(*args, **kwargs)

    @property
    def leistungsmodul_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="leistungsmodul").price)

    @property
    def stromgrundpreis_gesamt(self):
        return round(float(self.grundpreis) * 12 * int(self.zeitraum), 2)

    @staticmethod
    def priceInflation(pricePerYear, increasePerYear, years):
        sumPrice = 0
        priceList = []
        for i in range(years):
            sumPrice += pricePerYear
            priceList.append(sumPrice)
            pricePerYear = pricePerYear * (1.0 + increasePerYear)
        return sumPrice, priceList

    def get_arbeitspreis_and_list(self):
        if not hasattr(self, "_arbeitspreis_and_list"):
            self._arbeitspreis_and_list = self.priceInflation(
                float(self.arbeitspreis) / 100 * float(self.verbrauch),
                float(self.prognose) / 100,
                int(self.zeitraum),
            )
        return self._arbeitspreis_and_list

    @property
    def arbeitspreis_gesamt(self):
        arb_ges, _ = self.get_arbeitspreis_and_list()
        return round(arb_ges, 2)

    @property
    def arbeits_liste(self):
        _, arb_liste = self.get_arbeitspreis_and_list()
        return arb_liste

    @property
    def erzProJahr(self):
        direction_map = {"Sud": "erzeugung_sued", "Ost/West": "erzeugung_ost_west"}
        direction = str(self.ausrichtung)
        if direction in direction_map:
            return AndereKonfigurationWerte.objects.get(
                name=direction_map[direction]
            ).value
        else:
            return 0.00

    @property
    def get_komplexity(self):
        complexity_map = {
            "einfach, einfach erreichbar": "einfach_einfach_erreichbar",
            "einfach, schwer erreichbar": "einfach_schwer_erreichbar",
            "komplex, einfach erreichbar": "komplex_einfach_erreichbar",
            "komplex, schwer erreichbar": "komplex_schwer_erreichbar",
            "sehr komplex": "sehr_komplex",
        }
        complexity = str(self.komplex)
        if complexity in complexity_map:
            return AndereKonfigurationWerte.objects.get(
                name=complexity_map[complexity]
            ).value
        else:
            return 0.00

    """

    CALCULATING   SOLAR MODULE PARAMETERS  

    """

    @staticmethod
    def get_values():
        return {obj.name: obj.zuschlag for obj in SolarModulePreise.objects.all()}

    @staticmethod
    def get_prices():
        return {obj.name: obj.price for obj in OptionalAccessoriesPreise.objects.all()}

    @staticmethod
    def get_module_prices():
        return {obj.name: obj.price for obj in SolarModulePreise.objects.all()}

    def calculate_price(self, model, name, multiplier):
        try:
            multiplier = int(multiplier)
        except ValueError:
            multiplier = 0
        price = get_price(model, name)
        return price * multiplier

    @property
    def modulleistung_price(self):
        prices = self.get_prices()
        return float(prices[ACCESSORY_NAME])

    @property
    def solar_module_gesamt_preis(self):
        module_prices = self.get_module_prices()
        module_name = (
            self.solar_module if self.solar_module else "Phono Solar PS420M7GFH-18/VNH"
        )
        try:
            return float(module_prices[module_name]) * int(self.modulanzahl)
        except KeyError:
            # handle the error, maybe return a default value or raise a more descriptive error
            return 0.0

    @property
    def batteriespeicher_preis(self):
        batteriePreis = 0
        if self.anz_speicher > 0:
            leistungsmodulePreis = self.leistungsmodul_preis
            anz_speicher = int(self.anz_speicher)
            if self.speicher_model == "LUNA 2000-5-S0":
                batteriePreis = self.calculate_price(
                    OptionalAccessoriesPreise, "batteriemodul_huawei5", anz_speicher
                )
                batteriePreis = float(batteriePreis) + ceil(anz_speicher / 3) * float(
                    leistungsmodulePreis
                )
            elif self.speicher_model == "LUNA 2000-7-S1":
                batteriePreis = self.calculate_price(
                    OptionalAccessoriesPreise, "batteriemodul_huawei7", anz_speicher
                )
                batteriePreis = float(batteriePreis) + ceil(anz_speicher / 3) * float(
                    leistungsmodulePreis
                )
            elif self.speicher_model == "Vitocharge VX3 PV-Stromspeicher":
                batteriePreis = self.calculate_price(
                    OptionalAccessoriesPreise, "batteriemodul_viessmann", anz_speicher
                )
            return batteriePreis
        else:
            return 0

    @property
    def modulsumme_kWp(self):
        return self.modulleistungWp * self.modulanzahl / 1000


    @property
    def get_zuschlag(self):
        # Fetch all the values
        values = self.get_values()

        # Check if 'self.solar_module' is not None, else assign the default module name
        module_name = (
            self.solar_module
            if self.solar_module
            else ("Phono Solar PS420M7GFH-18/VNH")
        )
        # Return value based on module_name
        return float(values.get(module_name))

    @property
    def nutz_energie(self):
        nutzEnergie = float(self.verbrauch)
        if self.erzeugte_energie < nutzEnergie:
            nutzEnergie = float(self.erzProJahr) * float(self.modulsumme_kWp)
        if self.speicher and self.anz_speicher != 0:
            nutzEnergie = nutzEnergie * BATT_DICT[self.anz_speicher]
        else:
            nutzEnergie = nutzEnergie * DEFAULT_BATT_USAGE
        return round(nutzEnergie, 2)

    @property
    def restenergie(self):
        return float(self.verbrauch) - float(self.nutz_energie)

    @property
    def rest_strom_preis(self):
        reststromPreis, _ = self.priceInflation(
            float(self.arbeitspreis) / 100 * float(self.restenergie),
            float(self.prognose) / 100,
            self.zeitraum,
        )
        return round(reststromPreis, 2)

    @property
    def strom_ohne(self):
        return float(self.stromgrundpreis_gesamt) + float(self.arbeitspreis_gesamt)

    @property
    def kosten_rest_energie(self):
        return self.rest_strom_preis + self.stromgrundpreis_gesamt

    @property
    def einsp_pro_jahr(self):
        if self.modulsumme_kWp <= 10:
            return float(self.bis10kWp) * 0.01 * self.einsp_energie
        else:
            klZehn = float(self.bis10kWp) * 0.01 * (10 / self.modulsumme_kWp)
            grZehn = (
                float(self.bis40kWp)
                * 0.01
                * (self.modulsumme_kWp - 10)
                / self.modulsumme_kWp
            )
            return (klZehn + grZehn) * self.einsp_energie

    @property
    def erzeugte_energie(self):
        return round(float(self.erzProJahr) * float(self.modulsumme_kWp), 2)

    @property
    def einsp_energie(self):
        return self.erzeugte_energie - self.nutz_energie

    @property
    def einsp_verg(self):
        return round(self.einsp_pro_jahr * self.zeitraum, 2)

    @property
    def wallbox_kabel_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="kabelpreis").price)

    @property
    def harvi_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="harvi").price)

    @property
    def optimizer_preis(self):
        return float(OptionalAccessoriesPreise.objects.get(name="optimizer").price)

    @property
    def elwa_price(self):
        prices = self.get_prices()
        return float(prices["elwa_2"])

    @property
    def thor_price(self):
        prices = self.get_prices()
        return float(prices["ac_thor_3_kw"])

    @property
    def heizstab_price(self):
        prices = self.get_prices()
        return float(prices["heizstab"])

    @property
    def optimizer_full_preis(self):
        return self.anzOptimizer * self.optimizer_preis

    """

    CALCULATING   ANGEBOT SUMME  

    """

    @property
    def full_optimizer_preis(self):
        return self.anzOptimizer * self.get_optional_accessory_price("optimizer")

    @property
    def full_wallbox_preis(self):
        if self.wallbox_anzahl:
            preis = float(WallBoxPreise.objects.get(name=str(self.wallboxtyp)).price)
            preis *= self.wallbox_anzahl
            if self.kabelanschluss and self.kabelanschluss >= 10:
                preis += (self.kabelanschluss - 10) * self.get_optional_accessory_price(
                    "kabelpreis"
                )
            return preis
        else:
            return 0.00

    @property
    def full_accessories_price(self):
        accessories_price = 0
        if self.full_optimizer_preis:
            accessories_price += float(self.full_optimizer_preis)
        if self.full_wallbox_preis:
            accessories_price += float(self.full_wallbox_preis)
        if self.batteriespeicher_angebot_price:
            accessories_price += float(self.batteriespeicher_angebot_price)
        if self.notstrom:
            accessories_price += float(self.get_optional_accessory_price("backup_box"))
        if self.hub_included == True:
            accessories_price += float(self.get_optional_accessory_price("hub"))
        if self.elwa:
            accessories_price += float(self.elwa_price)
        if self.thor:
            accessories_price += float(self.thor_price)
        if self.heizstab:
            accessories_price += float(self.heizstab_price)
        return accessories_price

    @property
    def angebots_summe(self):
        def get_price(prefix, kw):
            name = prefix + str(kw)

            #return float(KwpPreise.objects.get(name=name).price)
            return (float(KwpPreise.objects.get(name=name).price)) * float(
                self.get_zuschlag
            )

        def get_garantie_price(kw, years):
            name = f"garantie{kw}_{years}"
            return float(WrGarantiePreise.objects.get(name=name).price)

        limits = [5, 7, 10, 12, 15, 20, 25, 30]
        ranges = (
            [(0, limits[0])]
            + list(zip(limits, limits[1:]))
            + [(limits[-1], float("30"))]
        )

        kwp = min(30, self.modulsumme_kWp)
        angebotsSumme = sum(
            (min(self.modulsumme_kWp, upper) - lower) * get_price("Preis", upper)
            for lower, upper in ranges
            if lower < kwp
        )

        angebotsSumme *= float(self.get_komplexity)
        angebotsSumme += float(self.full_accessories_price)

        if self.garantieWR != "keine":
            garantie_years = int(self.garantieWR.split(" ")[0])
            garantie_kw = next(
                kw
                for kw in [3, 4, 5, 6, 8, 10, 15, 16, 20, 25, 30]
                if kwp <= kw
            )
            angebotsSumme += get_garantie_price(garantie_kw, garantie_years)

        userAufschlag = float(self.user.users_aufschlag) / 100 + 1  # type: ignore
        angebotsSumme *= userAufschlag

        return angebotsSumme

    @property
    def kosten_pva(self):
        return float(self.angebots_summe) * float(
            1 + AndereKonfigurationWerte.objects.get(name="steuersatz").value
        )

    @property
    def abzug(self):
        res = 0.0
        if (
            self.kosten_pva
            and self.rest_strom_preis
            and self.stromgrundpreis_gesamt
            and self.einsp_verg
        ):
            res += (
                self.kosten_pva
                + self.rest_strom_preis
                + self.stromgrundpreis_gesamt
                - self.einsp_verg
            )
        return round(res, 2)

    @property
    def ersparnis(self):
        ersp = float(self.arbeitspreis_gesamt) - (
            float(self.kosten_pva)
            + float(self.rest_strom_preis)
            - float(self.einsp_verg)
        )
        return round(ersp, 2)

    @property
    def rest_liste(self):
        restenergie = float(self.verbrauch) - self.nutz_energie
        _, restListe = self.priceInflation(
            float(self.arbeitspreis) / 100 * restenergie,
            float(self.prognose) / 100,
            self.zeitraum,
        )
        for i in range(self.zeitraum):
            self.arbeits_liste[i] += float(self.grundpreis) * 12 * (i + 1)
            restListe[i] += float(self.grundpreis) * 12 * (i + 1)
            restListe[i] += self.kosten_pva
            restListe[i] -= self.einsp_pro_jahr * (i + 1)
        return restListe
