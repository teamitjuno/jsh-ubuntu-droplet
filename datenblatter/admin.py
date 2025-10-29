from django.contrib import admin
from .models import Datenblatter


class DatenblatterAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "speicher_module",
        "speicher_module_viessmann",
        "wechselrichter",
        "wechselrichter_map0",
        "wechselrichter_mb0",
        "wechselrichter_viessman",
        "backup_box",
        "smartguard",
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
                    "speicher_module_atmoce",
                    "speicher_module_viessmann",
                    "wechselrichter",
                    "wechselrichter_map0",
                    "wechselrichter_mb0",
                    "wechselrichter_viessman",
                    "backup_box",
                    "smartguard",
                    "backup_box_viessmann",
                    "viessmann_allgemeine_bedingungen",
                    "viessmann_versicherung_ausweis",
                    "ac_thor",
                    "ac_elwa",
                    "finanzierung",
                )
            },
        ),
    )
    # Add any other customizations here


admin.site.register(Datenblatter, DatenblatterAdmin)
