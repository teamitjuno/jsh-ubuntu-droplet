from django.contrib import admin
from prices.models import (
    ElektrikPreis,
    ModuleGarantiePreise,
    ModulePreise,
    WallBoxPreise,
    SolarModulePreise,
    OptionalAccessoriesPreise,
    AndereKonfigurationWerte,
    Prices,
)


class PricesInline(admin.TabularInline):
    model = Prices
    extra = 0


@admin.register(ElektrikPreis)
class ElektrikPreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
    )
    search_fields = ("name",)
    inlines = [PricesInline]


@admin.register(ModuleGarantiePreise)
class ModuleGarantiePreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
    )
    search_fields = ("name",)
    inlines = [PricesInline]


@admin.register(ModulePreise)
class ModulePreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
    )
    search_fields = ("name",)
    inlines = [PricesInline]


@admin.register(SolarModulePreise)
class SolarModulePreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "module_garantie",
        "leistungs_garantie",
        "in_stock",
    )
    search_fields = ("name",)


@admin.register(WallBoxPreise)
class WallBoxPreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "in_stock",
    )
    search_fields = ("name",)


@admin.register(OptionalAccessoriesPreise)
class OptionalAccessoriesPreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
    )
    search_fields = ("name",)
    inlines = [PricesInline]


@admin.register(AndereKonfigurationWerte)
class AndereKonfigurationWerteAdmin(admin.ModelAdmin):
    list_display = ("name", "value")
    search_fields = ("name",)


@admin.register(Prices)
class PricesAdmin(admin.ModelAdmin):
    list_display = (
        "elektrik_prices",
        "modul_prices",
        "modul_garantie_preise",
        "wallbox_prices",
        "optional_accessories_prices",
        "andere_preise",
    )
    list_select_related = (
        "elektrik_prices",
        "modul_prices",
        "modul_garantie_preise",
        "wallbox_prices",
        "optional_accessories_prices",
        "andere_preise",
    )
    search_fields = (
        "elektrik_prices__name",
        "modul_prices__name",
        "modul_garantie_preise__name",
        "wallbox_prices__name",
        "optional_accessories_prices__name",
        "andere_preise__name",
    )
    autocomplete_fields = (
        "elektrik_prices",
        "modul_prices",
        "modul_garantie_preise",
        "wallbox_prices",
        "optional_accessories_prices",
        "andere_preise",
    )
