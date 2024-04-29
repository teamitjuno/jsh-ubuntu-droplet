# from django.contrib import admin
# from invoices.models import ElectricInvoice, KundenData, Position


# class PositionInline(admin.TabularInline):
#     model = Position
#     extra = 1
#     min_num = 1
#     can_delete = True


# class KundenDataInline(admin.StackedInline):
#     model = KundenData
#     extra = 0
#     min_num = 1
#     max_num = 1
#     can_delete = False


# class ElectricInvoiceAdmin(admin.ModelAdmin):
#     list_display = ("invoice_id", "current_date", "user", "is_locked")
#     search_fields = ("invoice_id", "current_date", "user__username")
#     list_filter = ("is_locked", "user")
#     readonly_fields = ("invoice_id", "current_date")
#     inlines = [KundenDataInline, PositionInline]
#     change_form_template = "admin/invoices/ElectricInvoice/change_form.html"

#     def save_related(self, request, form, formsets, change):
#         if not change:  # Only lock invoice on creation
#             instance = form.instance
#             instance.is_locked = True
#             instance.save()
#         super().save_related(request, form, formsets, change)


# admin.site.register(ElectricInvoice, ElectricInvoiceAdmin)


# # from django.contrib import admin
# # from django.urls import reverse
# # from django.utils.html import format_html
# # from .models import (
# #     ElectricInvoice,
# #     KundenData,
# #     BestuckungsmaterialZahlerschrank,
# #     LeitungSchutzSchalter,
# #     SLS,
# #     USS,
# #     ZahlerKabel,
# #     Mantelleitung,
# #     KabelKanal,
# #     KleinVerteiler,
# #     HauptLeitungsAbzweigKleme,
# # )


# # class KundenDataInline(admin.TabularInline):
# #     model = KundenData
# #     extra = 0


# # class BestuckungsmaterialZahlerschrankInline(admin.TabularInline):
# #     model = BestuckungsmaterialZahlerschrank
# #     extra = 0


# # class LeitungSchutzSchalterInline(admin.TabularInline):
# #     model = LeitungSchutzSchalter
# #     extra = 0


# # # class SLSInline(admin.TabularInline):
# # #     model = SLS
# # #     extra = 0


# # class USSInline(admin.TabularInline):
# #     model = USS
# #     extra = 0


# # class ZahlerKabelInline(admin.TabularInline):
# #     model = ZahlerKabel
# #     extra = 0


# # class MantelleitungInline(admin.TabularInline):
# #     model = Mantelleitung
# #     extra = 0


# # class KabelKanalInline(admin.TabularInline):
# #     model = KabelKanal
# #     extra = 0


# # class KleinVerteilerInline(admin.TabularInline):
# #     model = KleinVerteiler
# #     extra = 0


# # class HauptLeitungsAbzweigKlemmeInline(admin.TabularInline):
# #     model = HauptLeitungsAbzweigKleme
# #     extra = 0

# # # class SLSAdmin(admin.ModelAdmin):
# # #     list_display = ("sls", "quantity", "invoice")
# # #     list_filter = [
# # #         "invoice",
# # #     ]
# # class ElectricInvoiceAdmin(admin.ModelAdmin):
# #     list_display = ("invoice_id", "current_date", "user", "is_locked", "view_details_link")
# #     search_fields = ("invoice_id", "user__username")
# #     list_filter = ("is_locked",)
# #     inlines = [
# #         KundenDataInline,
# #         BestuckungsmaterialZahlerschrankInline,
# #         LeitungSchutzSchalterInline,
# #         USSInline,
# #         ZahlerKabelInline,
# #         MantelleitungInline,
# #         KabelKanalInline,
# #         KleinVerteilerInline,
# #         HauptLeitungsAbzweigKlemmeInline,
# #     ]

# #     def view_details_link(self, obj):
# #         url = reverse("invoices:invoice_detail_1", args=[str(obj.pk)])
# #         return format_html('<a href="{}">View Details</a>', url)

# #     view_details_link.short_description = "Details"


# # admin.site.register(ElectricInvoice, ElectricInvoiceAdmin)
# # # admin.site.register(SLS, SLSAdmin)


# # # class KundenDataInline(admin.TabularInline):
# # #     model = KundenData
# # #     extra = 1

# # # class BestuckungsmaterialZahlerschrankInline(admin.TabularInline):
# # #     model = BestuckungsmaterialZahlerschrank
# # #     extra = 1


# # # class KabelKanalInline(admin.TabularInline):
# # #     model = KabelKanal
# # #     extra = 1


# # # class MantelleitungInline(admin.TabularInline):
# # #     model = Mantelleitung
# # #     extra = 1


# # # class ZahlerKabelInline(admin.TabularInline):
# # #     model = ZahlerKabel
# # #     extra = 1


# # # class KleinVerteilerInline(admin.TabularInline):
# # #     model = KleinVerteiler
# # #     extra = 1


# # # class LeitungSchutzSchalterInline(admin.TabularInline):
# # #     model = LeitungSchutzSchalter
# # #     extra = 1


# # # class SLSInline(admin.TabularInline):
# # #     model = SLS
# # #     extra = 1


# # # class USSInline(admin.TabularInline):
# # #     model = USS
# # #     extra = 1


# # # class HauptLeitungsAbzweigKlemeInline(admin.TabularInline):
# # #     model = HauptLeitungsAbzweigKleme
# # #     extra = 1


# # # class ElectricInvoiceAdmin(admin.ModelAdmin):
# # #     search_fields = ["invoice_id"]
# # #     list_display = (
# # #         "invoice_id",
# # #         "user",
# # #         "is_locked",

# # #     )
# # #     list_filter = (
# # #         "user",
# # #         "is_locked",
# # #         "created_at",
# # #         "updated_at",
# # #     )
# # #     inlines = [
# # #         BestuckungsmaterialZahlerschrankInline,
# # #         KabelKanalInline,
# # #         MantelleitungInline,
# # #         ZahlerKabelInline,
# # #         KleinVerteilerInline,
# # #         LeitungSchutzSchalterInline,
# # #         SLSInline,
# # #         USSInline,
# # #         HauptLeitungsAbzweigKlemeInline,
# # #     ]

# # # class KundenDataAdmin(admin.ModelAdmin):
# # #     list_display = (
# # #             "invoice"
# # #             "kunden_name",
# # #             "kunden_strasse",
# # #             "kunden_plz_ort",
# # #             "standort",
# # #             "netz_typ",
# # #             "zahlerschranken",
# # #     )
# # #     list_filter = [
# # #         "invoice",
# # #     ]
# # # class BestuckungsmaterialZahlerschrankAdmin(admin.ModelAdmin):
# # #     list_display = ("b_material", "quantity", "invoice")
# # #     list_filter = [
# # #         "invoice",
# # #     ]


# # # class USSAdmin(admin.ModelAdmin):
# # #     list_display = ("uss", "quantity", "invoice")
# # #     list_filter = ["invoice"]


# # # class KabelKanalAdmin(admin.ModelAdmin):
# # #     list_display = ("kabelkanal", "length", "invoice")
# # #     list_filter = ["invoice"]


# # # class ZahlerKabelAdmin(admin.ModelAdmin):
# # #     list_display = ("zahler_kabel", "length", "invoice")
# # #     list_filter = ["invoice"]


# # # class KleinVerteilerAdmin(admin.ModelAdmin):
# # #     list_display = ("klein_verteiler", "quantity", "invoice")
# # #     list_filter = [
# # #         "invoice",
# # #     ]


# # # class MantelleitungAdmin(admin.ModelAdmin):
# # #     list_display = ("mantelleitung", "length", "invoice")
# # #     list_filter = [
# # #         "invoice",
# # #     ]


# # # class KleineTeileAdmin(admin.ModelAdmin):
# # #     list_display = ("kleine_teile", "quantity", "invoice")
# # #     list_filter = [
# # #         "invoice",
# # #     ]


# # # class HauptLeitungsAbzweigKlemeAdmin(admin.ModelAdmin):
# # #     list_display = ("hauptabzweigklemme", "quantity", "invoice")
# # #     list_filter = [
# # #         "invoice",
# # #     ]


# # # class LeitungSchutzSchalterAdmin(admin.ModelAdmin):
# # #     list_display = ("leitungschutzschalter", "quantity", "invoice")
# # #     list_filter = [
# # #         "invoice",
# # #     ]


# # # admin.site.register(ElectricInvoice, ElectricInvoiceAdmin)
# # # admin.site.register(BestuckungsmaterialZahlerschrank, BestuckungsmaterialZahlerschrankAdmin)
# # # admin.site.register(Mantelleitung, MantelleitungAdmin)
# # # admin.site.register(KabelKanal, KabelKanalAdmin)
# # # admin.site.register(ZahlerKabel, ZahlerKabelAdmin)
# # # admin.site.register(KleinVerteiler, KleinVerteilerAdmin)
# # # admin.site.register(SLS, SLSAdmin)
# # # admin.site.register(USS, USSAdmin)
# # # admin.site.register(HauptLeitungsAbzweigKleme, HauptLeitungsAbzweigKlemeAdmin)
# # # admin.site.register(LeitungSchutzSchalter, LeitungSchutzSchalterAdmin)
