from django.contrib import admin
from .models import VertriebAngebot
from django.contrib import admin
from .models import VertriebAngebot


class VertriebAngebotAdmin(admin.ModelAdmin):
    list_display = (
        "angebot_id",
        "user",
        "status",
        "status_pva",
        "zoho_id",
        "angebot_zoho_id",
        "angebot_id_assigned",
        "zoho_kundennumer",
        "name",
        "termine_text",
        "is_locked",
        "angebotsumme",
    )

    search_fields = (
        "angebot_id",
        "name",
        "zoho_id",
        "angebot_zoho_id",
        "zoho_kundennumer",
        "user__username",
        "angebotsumme",
    )

    list_filter = (
        "user",
        "status",
        "is_locked",
        "angebot_id_assigned",
    )

    readonly_fields = (
        "angebot_id",
        "status_change_date",
        "solar_module_angebot_price",
        "batteriespeicher_angebot_price",
        "wallbox_angebot_price",
        "notstrom_angebot_price",
        "eddi_angebot_price",
        "optimizer_angebot_price",
        "angebotsumme",
    )
    change_form_template = "admin/vertrieb_interface/VertriebAngebot/change_form.html"

    fieldsets = (
        (
            "Allgemeine Informationen",
            {
                "fields": (
                    "angebot_id",
                    "user",
                    "is_locked",
                    "angebot_id_assigned",
                    "termine_text",
                    "termine_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "ZOHO Informationen",
            {
                "fields": (
                    "zoho_kundennumer",
                    "zoho_id",
                    "angebot_zoho_id",
                    "status",
                    "status_change_date",
                    "name_first_name",
                    "name_last_name",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Kunde Informationen",
            {
                "fields": (
                    "anrede",
                    "name",
                    "email",
                    "firma",
                    "strasse",
                    "ort",
                    "anlagenstandort",
                    "notizen",
                    "text_for_email",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Angebot Kalkulationsfelder",
            {
                "fields": (
                    "verbrauch",
                    "grundpreis",
                    "arbeitspreis",
                    "prognose",
                    "zeitraum",
                    "bis10kWp",
                    "bis40kWp",
                    "ausrichtung",
                    "komplex",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Speicher und Wallbox Felder",
            {
                "fields": (
                    "hersteller",
                    "wechselrichter_model",
                    "speicher_model",
                    "anz_speicher",
                    "wallboxtyp",
                    "wallbox_anzahl",
                    "kabelanschluss",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Module & Zubehör'",
            {
                "fields": (
                    "solar_module",
                    "modulleistungWp",
                    "modulanzahl",
                    "garantieWR",
                    "eddi",
                    "notstrom",
                    "anzOptimizer",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Anschluss und Ticket Details",
            {
                "fields": (
                    "module_ticket",
                    "modul_anzahl_ticket",
                    "optimizer_ticket",
                    "batteriemodule_ticket",
                    "notstrom_ticket",
                    "eddi_ticket",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Preisdetails",
            {
                "fields": (
                    "indiv_price_included",
                    "indiv_price",
                    "solar_module_angebot_price",
                    "batteriespeicher_angebot_price",
                    "wallbox_angebot_price",
                    "notstrom_angebot_price",
                    "eddi_angebot_price",
                    "optimizer_angebot_price",
                    "angebotsumme",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "DEBUG ANGEBOT_DATA",
            {
                "fields": ("ag_data",),
                "classes": ("collapse",),
            },
        ),
    )
    ordering = ("-current_date",)

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "is_locked":
            formfield.label = "Bearbeitung gesperrt"  # type: ignore
        return formfield


admin.site.register(VertriebAngebot, VertriebAngebotAdmin)
