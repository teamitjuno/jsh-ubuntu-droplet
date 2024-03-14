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
        "wall_box_viessmann",
        "wechselrichter",
        "wechselrichter_viessmann",
        "backup_box",
        "backup_box_viessmann",
        "optimizer",
        "optimizer_viessmann",
    ]

    fieldsets = (
        (
            "Solar Modules",
            {"fields": ("solar_module_1", "solar_module_2", "solar_module_3", "solar_module_4",)},
        ),
        (
            "Other Components",
            {
                "fields": (
                    "optimizer",
                    "optimizer_viessmann",
                    "speicher_module",
                    "speicher_module_viessmann",
                    "wall_box",
                    "wall_box_viessmann",
                    "wechselrichter",
                    "wechselrichter_viessmann",
                    "backup_box",
                    "backup_box_viessmann",
                )
            },
        ),
    )
    # Add any other customizations here


admin.site.register(Datenblatter, DatenblatterAdmin)
