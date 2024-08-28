from django.contrib import admin
from .models import Datenblatter


class DatenblatterAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "speicher_module",
        "speicher_module_viessmann",
        "wechselrichter",
        "wechselrichter_viessman",
        "backup_box",
        "backup_box_viessmann",
        "optimizer",
        "optimizer_viessmann",
    ]

    fieldsets = (
        (
            "Other Components",
            {
                "fields": (
                    "optimizer",
                    "huawei_smartmeter_dtsu",
                    "huawei_smartmeter_emma",
                    "huawei_smart_energie_controller",
                    "optimizer_viessmann",
                    "viessmann_tigo",
                    "speicher_module",
                    "speicher_module_huawei7",
                    "speicher_module_viessmann",
                    "wechselrichter",
                    "wechselrichter_viessman",
                    "backup_box",
                    "backup_box_viessmann",
                    "viessmann_allgemeine_bedingungen",
                    "viessmann_versicherung_ausweis",
                    "ac_thor",
                    "finanzierung",
                )
            },
        ),
    )
    # Add any other customizations here


admin.site.register(Datenblatter, DatenblatterAdmin)
