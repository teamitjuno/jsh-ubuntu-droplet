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


class ModulePreise(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(name, price=0.00):
        new_position = ModulePreise.objects.create(
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
    in_stock = models.BooleanField(default=True, null=True, blank=True)

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

    def __str__(self) -> str:
        return f"{self.price}"

    @staticmethod
    def add_position(name, price=0.00):
        new_position = OptionalAccessoriesPreise.objects.create(
            name=name, price=price
        )
        new_position.save()


class AndereKonfigurationWerte(models.Model):
    name = models.CharField(max_length=255, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self) -> str:
        return f"{self.value}"

    @staticmethod
    def add_position(name, value=0.00):
        new_position = AndereKonfigurationWerte.objects.create(name=name, value=value)
        new_position.save()


class Prices(models.Model):
    elektrik_prices = models.ForeignKey(ElektrikPreis, on_delete=models.CASCADE)
    modul_prices = models.ForeignKey(ModulePreise, on_delete=models.CASCADE)
    modul_garantie_preise = models.ForeignKey(
        WrGarantiePreise, on_delete=models.CASCADE
    )
    wallbox_prices = models.ForeignKey(WallBoxPreise, on_delete=models.CASCADE)
    optional_accessories_prices = models.ForeignKey(
        OptionalAccessoriesPreise, on_delete=models.CASCADE
    )
    andere_preise = models.ForeignKey(
        AndereKonfigurationWerte, on_delete=models.CASCADE
    )
