from django.contrib import admin
from prices.models import (
    ElektrikPreis,
    WrGarantiePreise,
    KwpPreise,
    WallBoxPreise,
    SolarModulePreise,
    OptionalAccessoriesPreise,
    WrTauschPreise,
    Sonderrabatt,
    AndereKonfigurationWerte,
    PLZAufpreisNachkauf,
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


@admin.register(WrGarantiePreise)
class ModuleGarantiePreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
    )
    search_fields = ("name",)
    inlines = [PricesInline]


@admin.register(KwpPreise)
class KwpPreisAdmin(admin.ModelAdmin):
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
        "zuschlag",
        "filename",
        "datenblatt",
    )
    search_fields = ("name",)


@admin.register(WallBoxPreise)
class WallBoxPreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "price_other",
        "pdf_text",
        "in_stock",
        "filename",
        "datenblatt",
    )
    search_fields = ("name",)


@admin.register(OptionalAccessoriesPreise)
class OptionalAccessoriesPreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "price_other",
        "pdf_name",
        "pdf_text",
    )
    search_fields = ("name",)
    inlines = [PricesInline]



@admin.register(WrTauschPreise)
class WrTauschPreisAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "pdf_name",
        "pdf_text",
    )
    search_fields = ("name",)


@admin.register(Sonderrabatt)
class SonderrabattAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "prozentsatz",
        "fixbetrag",
        "is_active",
    )
    search_fields = ("name",)
    inlines = [PricesInline]


@admin.register(AndereKonfigurationWerte)
class AndereKonfigurationWerteAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "text")
    search_fields = ("name",)


@admin.register(PLZAufpreisNachkauf)
class PLZAufpreisNachkaufAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "text")
    search_fields = ("name",)


@admin.register(Prices)
class PricesAdmin(admin.ModelAdmin):
    list_display = (
        "elektrik_prices",
        "modul_prices",
        "wr_garantie_preise",
        "plzAufpreis_nachverkauf",
        "wallbox_prices",
        "optional_accessories_prices",
        "sonder_rabatt",
        "andere_preise",
    )
    list_select_related = (
        "elektrik_prices",
        "modul_prices",
        "wr_garantie_preise",
        "plzAufpreis_nachverkauf",
        "wallbox_prices",
        "optional_accessories_prices",
        "sonder_rabatt",
        "andere_preise",
    )
    search_fields = (
        "elektrik_prices__name",
        "modul_prices__name",
        "wr_garantie_preise__name",
        "plzAufpreis_nachverkauf__name",
        "wallbox_prices__name",
        "optional_accessories_prices__name",
        "sonder_rabatt__name",
        "andere_preise__name",
    )
    autocomplete_fields = (
        "elektrik_prices",
        "modul_prices",
        "wr_garantie_preise",
        "plzAufpreis_nachverkauf",
        "wallbox_prices",
        "optional_accessories_prices",
        "sonder_rabatt",
        "andere_preise",
    )
