# from django.contrib import admin
# from .models import ElectricCalendar, Position, PVAKlein1
# from .forms import ElectricCalendarForm, PositionForm, PVAKlein1Form


# class PositionInline(admin.TabularInline):
#     model = Position
#     form = PositionForm
#     extra = 0  # Number of extra empty rows to display


# class PVAKlein1Inline(admin.TabularInline):
#     model = PVAKlein1
#     form = PVAKlein1Form
#     extra = 0  # Number of extra empty rows to display


# class ElectricCalendarAdmin(admin.ModelAdmin):
#     form = ElectricCalendarForm
#     list_display = [
#         "calendar_id",
#         "zoho_id",
#         "current_date",
#         "user",
#         "is_locked",
#         "kundenname",
#         "elektriktermin_am",
#         "kundenname_rawdata",
#         "termin_best_tigt",
#     ]
#     search_fields = ["calendar_id", "zoho_id", "kundenname"]
#     list_filter = ["user", "current_date", "is_locked", "elektriktermin_am"]
#     ordering = ["current_date"]
#     inlines = [PositionInline, PVAKlein1Inline]


# admin.site.register(ElectricCalendar, ElectricCalendarAdmin)
