from django.contrib import admin
from django.contrib import admin
from .models import VertriebAngebot, VertriebTicket
from .models import Editierbarer_Text, Dokument_PDF, CustomLogEntry


class VertriebAngebotAdmin(admin.ModelAdmin):
    list_display = (
        "angebot_id",
        "user",
        "status",
        "status_pva",
        "zoho_id",
        "angebot_zoho_id",
        "angenommenes_angebot",
        "angebot_id_assigned",
        "zoho_kundennumer",
        "name",
        "termine_text",
        "is_locked",
        "angebotsumme",
        "updated_at",
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
        "status_change_date",
        "solar_module_angebot_price",
        "batteriespeicher_angebot_price",
        "wallbox_angebot_price",
        "notstrom_angebot_price",
        "optimizer_angebot_price",
        "angebotsumme",
        "angebot_pdf",
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
                    "angebot_pdf",
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
                    "angenommenes_angebot",
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
            "PV-Anlage",
            {
                "fields": (
                    "solar_module",
                    "modulleistungWp",
                    "modulanzahl",
                    "hersteller",
                    "wechselrichter_model",
                    "speicher_model",
                    "anz_speicher",
                    "smartmeter_model",
                    "garantieWR",
                    "anzOptimizer",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Zubehör",
            {
                "fields": (
                    "notstrom",
                    "ersatzstrom",
                    "smartDongleLte",
                    "thor",
                    "heizstab",
                    "elwa",
                    "apzFeld",
                    "zaehlerschrank",
                    "potentialausgleich",
                    "beta_platte",
                    "metall_ziegel",
                    "prefa_befestigung",
                    "geruestKunde",
                    "geruestOeffentlich",
                    "dachhakenKunde",
                    "midZaehler",
                    "wandhalterung_fuer_speicher",
                    "anz_wandhalterung_fuer_speicher",
                    "wallboxtyp",
                    "wallbox_anzahl",
                    "kabelanschluss",
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
                    "optimizer_angebot_price",
                    "rabatt",
                    "rabattsumme",
                    "ausweisung_rabatt",
                    "genehmigung_rabatt",
                    "sonderrabatt_included",
                    "sonderrabatt",
                    "angebotsumme",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Finanzierung",
            {
                "fields": (
                    "finanzierung",
                    "anzahlung",
                    "nettokreditbetrag",
                    "monatliche_rate",
                    "laufzeit",
                    "sollzinssatz",
                    "effektiver_zins",
                    "gesamtkreditbetrag",
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


class VertriebTicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_id",
        "user",
        "status",
        "status_pva",
        "zoho_id",
        "angebot_zoho_id",
        "angenommenes_angebot",
        "angebot_id_assigned",
        "zoho_kundennumer",
        "name",
        "is_locked",
        "angebotsumme",
        "updated_at",
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
        "status_change_date",
        "solar_module_angebot_price",
        "batteriespeicher_angebot_price",
        "wallbox_angebot_price",
        "notstrom_angebot_price",
        "optimizer_angebot_price",
        "angebotsumme",
        "ticket_pdf",
    )
    change_form_template = "admin/vertrieb_interface/VertriebTicket/change_form.html"

    fieldsets = (
        (
            "Allgemeine Informationen",
            {
                "fields": (
                    "ticket_id",
                    "user",
                    "is_locked",
                    "angebot_id_assigned",
                    "ticket_pdf",
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
                    "angenommenes_angebot",
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
            "PV-Anlage",
            {
                "fields": (
                    "solar_module",
                    "modulleistungWp",
                    "modulanzahl",
                    "speicher_model",
                    "anz_speicher",
                    "smartmeter_model",
                    "anzOptimizer",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Zubehör",
            {
                "fields": (
                    "notstrom",
                    "ersatzstrom",
                    "smartDongleLte",
                    "thor",
                    "heizstab",
                    "elwa",
                    "apzFeld",
                    "zaehlerschrank",
                    "potentialausgleich",
                    "beta_platte",
                    "metall_ziegel",
                    "prefa_befestigung",
                    "geruestKunde",
                    "geruestOeffentlich",
                    "dachhakenKunde",
                    "midZaehler",
                    "wandhalterung_fuer_speicher",
                    "anz_wandhalterung_fuer_speicher",
                    "wallboxtyp",
                    "wallbox_anzahl",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Preisdetails",
            {
                "fields": (
                    "solar_module_angebot_price",
                    "batteriespeicher_angebot_price",
                    "wallbox_angebot_price",
                    "notstrom_angebot_price",
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



class EditierbarerTextInline(admin.TabularInline):
    """
    Defines an inline admin descriptor for Editierbarer_Text model.
    This is used for displaying editable text within the Dokument_PDF admin view.
    """

    model = (
        Dokument_PDF.editable_texts.through
    )  # This accesses the through model of the ManyToMany relation
    extra = 1  # Specifies the number of extra forms in the inline formset.


@admin.register(Editierbarer_Text)
class EditierbarerTextAdmin(admin.ModelAdmin):
    list_display = ("identifier", "content", "x", "y", "font_size", "last_updated")
    list_filter = ("font_size", "last_updated")
    search_fields = ("identifier", "content")
    fieldsets = (
        ("Allgemein", {"fields": ("identifier", "content")}),
        (
            "Schriftart-Einstellungen",
            {
                "fields": ("font", "font_size"),
                "classes": ("collapse",),
            },
        ),
        (
            "Position",
            {
                "fields": ("x", "y"),
                "classes": ("collapse",),
            },
        ),
        (
            "Update-Informationen",
            {
                "fields": ("last_updated",),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("last_updated",)


@admin.register(CustomLogEntry)
class CustomLogEntryAdmin(admin.ModelAdmin):
    list_display = ("user_id", "content_type_id", "object_id")
    list_filter = ("user_id", "change_message")
    search_fields = ("user_id", "object_id", "change_message")
    fieldsets = (
        ("Allgemein", {"fields": ("object_id", "object_repr", "action_flag", "change_message")}),
    )
    readonly_fields = ("user_id",)


@admin.register(Dokument_PDF)
class DokumentPDFAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title",)
    inlines = [EditierbarerTextInline]
    fieldsets = (
        (None, {"fields": ("title",)}),
        (
            "Date Information",
            {
                "fields": ("created_at", "last_modified"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at", "last_modified")


# Check if the model is registered
if Dokument_PDF.editable_texts.through in admin.site._registry:
    admin.site.unregister(Dokument_PDF.editable_texts.through)

admin.site.register(VertriebAngebot, VertriebAngebotAdmin)
admin.site.register(VertriebTicket, VertriebTicketAdmin)
