from django.db import models


class ElektrikPreis(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(name, price=0.00):
        new_position = ElektrikPreis.objects.create(
            name=name, price=price
        )
        new_position.save()


class WrGarantiePreise(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(name, price=0.00):
        new_position = WrGarantiePreise.objects.create(
            name=name, price=price
        )
        new_position.save()


class KwpPreise(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(name, price=0.00):
        new_position = KwpPreise.objects.create(
            name=name, price=price
        )
        new_position.save()


class SolarModulePreise(models.Model):
    name = models.CharField(max_length=255, unique=True)
    module_garantie = models.CharField(max_length=100, blank=True, null=True)
    leistungs_garantie = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    zuschlag = models.DecimalField(max_digits=10, decimal_places=3, default=1.00)
    quantity = models.IntegerField(blank=True, null=True)
    in_stock = models.BooleanField(default=True)
    filename = models.CharField(max_length=255, default="Solarmodule")
    datenblatt = models.FileField(upload_to="uploads/", blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(name, price=0.00):
        new_position = SolarModulePreise.objects.create(
            name=name, price=price
        )
        new_position.save()


class WallBoxPreise(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_text = models.TextField(help_text="Inhalt", default="<<kein editierbarer text>>")
    in_stock = models.BooleanField(default=True, null=True, blank=True)
    filename = models.CharField(max_length=255, default="Wallbox")
    datenblatt = models.FileField(upload_to="uploads/", blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(
        name, price=0.00, in_stock=True
    ):
        new_position = WallBoxPreise.objects.create(
            name=name,
            price=price,
            in_stock=in_stock,
        )
        new_position.save()


class OptionalAccessoriesPreise(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_name = models.CharField(max_length=255, default="", blank=True)
    pdf_text = models.TextField(help_text="Inhalt" ,default="", blank=True)

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(name, price=0.00):
        new_position = OptionalAccessoriesPreise.objects.create(
            name=name, price=price
        )
        new_position.save()


class Sonderrabatt(models.Model):
    name = models.CharField(max_length=255, unique=True)
    prozentsatz = models.DecimalField(max_digits=10, decimal_places=2)
    fixbetrag = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name}"

    @staticmethod
    def add_position(name, prozentsatz=0.00, fixbetrag=0.00):
        new_position = Sonderrabatt.objects.create(
            name=name, price=prozentsatz, fixbetrag=fixbetrag
        )
        new_position.save()



class AndereKonfigurationWerte(models.Model):
    name = models.CharField(max_length=255, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=3)
    text = models.CharField(max_length=255, default="", blank=True)

    def __str__(self) -> str:
        return f"{self.value}"

    @staticmethod
    def add_position(name, value=0.00, text=""):
        new_position = AndereKonfigurationWerte.objects.create(name=name, value=value, text=text)
        new_position.save()


class Prices(models.Model):
    elektrik_prices = models.ForeignKey(ElektrikPreis, on_delete=models.CASCADE)
    modul_prices = models.ForeignKey(KwpPreise, on_delete=models.CASCADE)
    wr_garantie_preise = models.ForeignKey(
        WrGarantiePreise, on_delete=models.CASCADE
    )
    wallbox_prices = models.ForeignKey(WallBoxPreise, on_delete=models.CASCADE)
    optional_accessories_prices = models.ForeignKey(
        OptionalAccessoriesPreise, on_delete=models.CASCADE
    )
    sonder_rabatt = models.ForeignKey(Sonderrabatt, on_delete=models.CASCADE)
    andere_preise = models.ForeignKey(
        AndereKonfigurationWerte, on_delete=models.CASCADE
    )
