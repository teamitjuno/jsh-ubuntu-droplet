from django.conf import settings
from django.urls import path, re_path
from django.conf.urls.static import static
from django.views import defaults as default_views
from authentication.api import LoginView, LogoutView
from invoices.views import home
from authentication.views import (
    update_vertrieblers,
    delete_unused_data,
    update_elektrikers,
    protected_schema_view,
    zoho_callback,
)

app_name = "authentication"

# General URL patterns for authentication and home page
general_patterns = [
    path("", home, name="home"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("auth/callback", zoho_callback, name="zoho_callback"),
]

# URL patterns related to updating various entities
update_patterns = [
    path("update_vertrieblers/", update_vertrieblers, name="update_vertrieblers"),
    path("delete_unused_data/", delete_unused_data, name="delete_unused_data"),
    path("admin/update_elektrikers/", update_elektrikers, name="update_elektrikers"),
    path("admin/schema/", protected_schema_view, name="schema_view"),
]

# URL patterns handling various HTTP error statuses
error_handling_patterns = [
    re_path(
        r"^400/$",
        default_views.bad_request,
        kwargs={"exception": Exception("Bad Request!")},
    ),
    re_path(
        r"^403/$",
        default_views.permission_denied,
        kwargs={"exception": Exception("Permission Denied")},
    ),
    re_path(
        r"^404/$",
        default_views.page_not_found,
        kwargs={"exception": Exception("Page not Found")},
    ),
    re_path(r"^500/$", default_views.server_error),
]

# Concatenation of all the URL pattern groups along with static file URL patterns
urlpatterns = (
    general_patterns
    + update_patterns
    + error_handling_patterns
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
