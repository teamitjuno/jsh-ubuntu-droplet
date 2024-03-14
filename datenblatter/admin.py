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
        "backup_box_viessman",
        "optimizer",
        "optimizer_viessman",
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
                    "optimizer_viessman",
                    "speicher_module",
                    "speicher_module_viessmann",
                    "wall_box",
                    "wall_box_viessman",
                    "wechselrichter",
                    "wechselrichter_viessman",
                    "backup_box",
                    "backup_box_viessman",
                )
            },
        ),
    )
    # Add any other customizations here


admin.site.register(Datenblatter, DatenblatterAdmin)
