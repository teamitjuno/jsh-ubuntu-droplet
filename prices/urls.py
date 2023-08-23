from django.urls import path
from .views import (
    SolarModulePreiseCreateView,
    SolarModulePreiseUpdateView,
    SolarModulePreiseDeleteView,
)

urlpatterns = [
    path(
        "create/",
        SolarModulePreiseCreateView.as_view(),
        name="solar_module_preise_create",
    ),
    path(
        "update/<int:pk>/",
        SolarModulePreiseUpdateView.as_view(),
        name="solar_module_preise_update",
    ),
    path(
        "delete/<int:pk>/",
        SolarModulePreiseDeleteView.as_view(),
        name="solar_module_preise_delete",
    ),
]
