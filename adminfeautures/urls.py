from django.urls import path
from adminfeautures.views import user_list_view, update_solar_module_preise_view, update_wallbox_preise_view, update_optional_accessories_preise_view, update_andere_konfiguration_werte_view, ViewAdminOrders, UpdateAdminAngebot

app_name = "adminfeautures"

urlpatterns = [
    path("user-list/", user_list_view, name="user_list"),
    path("user/<int:user_id>/orders/", ViewAdminOrders.as_view(), name="user-orders"),
    path(
        "adminfeautures/user/<int:user_id>/orders/",
        ViewAdminOrders.as_view(),
        name="view_admin_orders",
    ),
    path(
        "user/<int:user_id>/orders/<str:angebot_id>/",
        UpdateAdminAngebot.as_view(),
        name="update_admin_angebot",
    ),
    path('prices/update_solar_module_preise/<int:module_id>/', update_solar_module_preise_view, name='update_solar_module_preise'),
    path('prices/update_wallbox_preise/<int:wallbox_id>/', update_wallbox_preise_view, name='update_wallbox_preise'),
    path('prices/update_optional_accessories_preise/<int:accessories_id>/', update_optional_accessories_preise_view, name='update_optional_accessories_preise'),
    path('prices/update_andere_konfiguration_werte/<int:andere_konfiguration_id>/', update_andere_konfiguration_werte_view, name='update_andere_konfiguration_werte'),

]
