from django.contrib import admin
from .models import Datenblatter


class DatenblatterAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "solar_module_1",
        "solar_module_2",
        "solar_module_3",
        "solar_module_4",
        "speicher_module",
        "speicher_module_viessmann",
        "wall_box",
        "wall_box_viessman",
        "wechselrichter",
        "wechselrichter_viessman",
        "backup_box",
        "backup_box_viessmann",
        "optimizer",
        "optimizer_viessmann",
    ]

    fieldsets = (
        (
            "Solar Modules",
            {
                "fields": (
                    "solar_module_1",
                    "solar_module_2",
                    "solar_module_3",
                    "solar_module_4",
                )
            },
        ),
        (
            "Other Components",
            {
                "fields": (
                    "optimizer",
                    "huawei_power_sensor",
                    "huawei_smart_energie_controller",
                    "optimizer_viessmann",
                    "viessmann_tigo",
                    "speicher_module",
                    "speicher_module_viessmann",
                    "wall_box",
                    "wall_box_viessman",
                    "wechselrichter",
                    "wechselrichter_viessman",
                    "backup_box",
                    "backup_box_viessmann",
                    "viessmann_allgemeine_bedingungen",
                    "viessmann_versicherung_ausweis",
                    "ac_thor",
                )
            },
        ),
    )
    # Add any other customizations here


admin.site.register(Datenblatter, DatenblatterAdmin)
