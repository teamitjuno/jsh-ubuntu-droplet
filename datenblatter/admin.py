from django.contrib import admin
from .models import Datenblatter


class DatenblatterAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "solar_module_1",
        "solar_module_2",
        "solar_module_3",
        "speicher_module",
        "wall_box",
        "wechselrichter",
        "backup_box",
        "optimizer",
    ]

    fieldsets = (
        (
            "Solar Modules",
            {"fields": ("solar_module_1", "solar_module_2", "solar_module_3")},
        ),
        (
            "Other Components",
            {
                "fields": (
                    "optimizer",
                    "speicher_module",
                    "wall_box",
                    "wechselrichter",
                    "backup_box",
                )
            },
        ),
    )
    # Add any other customizations here


admin.site.register(Datenblatter, DatenblatterAdmin)
