from django.urls import path
from adminfeautures.views import user_list_view, ViewAdminOrders, UpdateAdminAngebot

app_name = "adminfeautures"

urlpatterns = [
    path("user-list/", user_list_view, name="user-list"),
    path("user/<int:user_id>/orders/", ViewAdminOrders.as_view(), name="user-orders"),
    path(
        "update_admin_angebot/<int:user_id>/<int:angebot_id>/",
        UpdateAdminAngebot.as_view(),
        name="update_admin_angebot",
    ),
    path(
        "adminfeautures/user/<int:user_id>/orders/",
        ViewAdminOrders.as_view(),
        name="view_admin_orders",
    ),
    path("user_list_view/", user_list_view, name="user_list_view"),
    path(
        "user/<int:user_id>/orders/<str:angebot_id>/",
        UpdateAdminAngebot.as_view(),
        name="update_admin_angebot",
    ),
]
