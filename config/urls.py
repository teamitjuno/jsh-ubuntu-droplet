from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.views import defaults as default_views
from invoices.views import handler403, handler404, handler500
from authentication.views import (
    update_vertrieblers,
    update_elektrikers,
    protected_schema_view,
)


def include_with_namespace(pattern_prefix, app_name):
    """Include patterns with namespace.

    Args:
        pattern_prefix (str): The prefix for the pattern.
        app_name (str): The application name.

    Returns:
        object: An include() object with specified namespace.
    """
    return include((pattern_prefix, app_name), namespace=app_name)


# Admin and Special Pages Paths
urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("adminfeautures/", include_with_namespace("adminfeautures.urls", "adminfeautures")),
    path("update_vertrieblers/", update_vertrieblers, name="update_vertrieblers"),
    path("update_elektrikers/", update_elektrikers, name="update_elektrikers"),
    path("admin/schema/", protected_schema_view, name="schema_view"),
]

# General Paths
urlpatterns += [
    path("", include("authentication.urls", namespace="authentication")),
    path("", include("vertrieb_interface.urls", namespace="vertrieb_interface")),
    path("proj/", include("projektant_interface.urls", namespace="projektant_interface")),
    path("elektriker_interface/", include("invoices.urls", namespace="invoices")),
    path("elektriker_kalender/", include("elektriker_kalender.urls", namespace="elektriker_kalender")),
]

# Error Handling Paths
error_handling_patterns = [
    re_path(r"^400/$", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")}),
    re_path(r"^403/$", default_views.permission_denied, kwargs={"exception": Exception("Permission Denied")}),
    re_path(r"^404/$", default_views.page_not_found, kwargs={"exception": Exception("Page not Found")}),
    re_path(r"^500/$", default_views.server_error),
]

# Adding additional error handling paths in DEBUG mode
if settings.DEBUG:
    error_handling_patterns += [
        re_path(r"^403/$", handler403),
        re_path(r"^404/$", handler404),
        re_path(r"^500/$", handler500),
    ]

urlpatterns += error_handling_patterns

# Static and Media Paths
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
