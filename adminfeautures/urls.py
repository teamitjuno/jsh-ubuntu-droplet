"""URL Configuration for the `adminfeatures` Django app.

The `urlpatterns` list routes URLs to views. For more information, please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""

from django.conf import settings
from django.urls import path, re_path
from django.conf.urls.static import static
from django.views import defaults as default_views
from adminfeautures.views import (
    user_list_view,
    update_solar_module_preise_view,
    update_wallbox_preise_view,
    update_optional_accessories_preise_view,
    update_andere_konfiguration_werte_view,
    avatar_upload_form,
    delete_user,
    test_delete_selected,
    PasswordUpdateView,
    ViewAdminOrders,
    UpdateAdminAngebot,
    DeleteAngebot,
    UserUpdateView,
    TopVerkauferContainerUpdateView,
    DeleteSelectedAngebots,
)

app_name = "adminfeautures"

# User management paths
user_management_patterns = [
    path("user-list/", user_list_view, name="user_list"),
    path("user/<int:pk>/edit/", UserUpdateView.as_view(), name="user-edit"),
    path("user/<int:pk>/delete/", delete_user, name="delete_user"),
    path("user/<int:pk>/change_password/", PasswordUpdateView.as_view(), name="change_password"),
    path("user/<int:user_id>/upload-avatar/", avatar_upload_form, name="upload_avatar"),
    path("user/<int:pk>/user-update/", UserUpdateView.as_view(), name="user-update"),
]

# User order management paths
user_order_management_patterns = [
    path("user/<int:user_id>/orders/", ViewAdminOrders.as_view(), name="user-orders"),
    path("user/<int:user_id>/orders/<str:angebot_id>/", UpdateAdminAngebot.as_view(), name="update_admin_angebot"),
    path("user/<int:user_id>/orders/delete/<str:angebot_id>/", DeleteAngebot.as_view(), name="delete_angebot"),
    path("user/<int:user_id>/orders/test-delete-selected/", test_delete_selected, name="test_delete_selected"),
    path("user/<int:user_id>/orders/delete-selected/", DeleteSelectedAngebots.as_view(), name="delete_selected_angebots"),
]

# Price management paths
price_management_patterns = [
    path("prices/update_solar_module_preise/<int:module_id>/", update_solar_module_preise_view, name="update_solar_module_preise"),
    path("prices/update_wallbox_preise/<int:wallbox_id>/", update_wallbox_preise_view, name="update_wallbox_preise"),
    path("prices/update_optional_accessories_preise/<int:accessories_id>/", update_optional_accessories_preise_view, name="update_optional_accessories_preise"),
    path("prices/update_andere_konfiguration_werte/<int:andere_konfiguration_id>/", update_andere_konfiguration_werte_view, name="update_andere_konfiguration_werte"),
]

# Error handling paths
error_handling_patterns = [
    re_path(r"^400/$", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")}),
    re_path(r"^403/$", default_views.permission_denied, kwargs={"exception": Exception("Permission Denied")}),
    re_path(r"^404/$", default_views.page_not_found, kwargs={"exception": Exception("Page not Found")}),
    re_path(r"^500/$", default_views.server_error),
]

urlpatterns = (
    user_management_patterns
    + user_order_management_patterns
    + price_management_patterns
    + error_handling_patterns
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

