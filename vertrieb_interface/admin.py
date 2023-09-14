from django.contrib import admin
from .models import VertriebAngebot


class VertriebAngebotAdmin(admin.ModelAdmin):
    list_display = (
        "angebot_id",
        "user",
        "status",
        "zoho_id",
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
        "zoho_kundennumer",
        "user__username",  # Search User model's username field
        "angebotsumme",
    )

    list_filter = (
        "user",
        "status",
        "is_locked",
    )

    readonly_fields = (
        "angebot_id",
        "zoho_id",
        "status_change_date",
        "zoho_kundennumer",
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
                    "zoho_id",
                    "status",
                    "status_change_date",
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
            "Kunde Informationen",
            {
                "fields": (
                    "zoho_kundennumer",
                    "anrede",
                    "name",
                    "email",
                    "firma",
                    "strasse",
                    "ort",
                    "anlagenstandort",
                    "notizen",
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
                    "anz_speicher",
                    "wallboxtyp",
                    "wallbox_anzahl",
                    "kabelanschluss",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Anlage Details",
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

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "is_locked":
            formfield.label = "Bearbeitung gesperrt"  # type: ignore
        return formfield


admin.site.register(VertriebAngebot, VertriebAngebotAdmin)
