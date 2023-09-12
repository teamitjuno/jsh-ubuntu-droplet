from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from django.views import defaults as default_views

from authentication.api import LoginView, LogoutView
from invoices.views import home
from authentication.views import (
    update_vertrieblers,
    update_elektrikers,
    protected_schema_view,
)

app_name = "authentication"

urlpatterns = [
    # General
    path("", home, name="home"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Updates
    path("update_vertrieblers/", update_vertrieblers, name="update_vertrieblers"),
    path("admin/update_elektrikers/", update_elektrikers, name="update_elektrikers"),
    path("admin/schema/", protected_schema_view, name="schema_view"),
    # Error handlers
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

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
