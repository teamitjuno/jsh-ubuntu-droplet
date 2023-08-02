from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls.static import static
from invoices.views import handler403, handler404, handler500
from authentication.views import (
    update_vertrieblers,
    update_elektrikers,
    protected_schema_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('adminfeautures/', include(('adminfeautures.urls', 'adminfeautures'), namespace='adminfeautures')),
    path(
        "update_vertrieblers/",
        update_vertrieblers,
        name="update_vertrieblers",
    ),
    path("update_elektrikers/", update_elektrikers, name="update_elektrikers"),
    path("admin/schema/", protected_schema_view, name="schema_view"),
    path("/", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
    path("", include("authentication.urls", namespace="authentication")),
    path("", include("vertrieb_interface.urls", namespace="vertrieb_interface")),
    path("elektriker_interface/", include("invoices.urls", namespace="invoices")),
    path(
        "elektriker_kalender",
        include("elektriker_kalender.urls", namespace="elektriker_kalender"),
    ),
]

# Error handlers
if settings.DEBUG:
    urlpatterns += [
        re_path(r"^403/$", handler403),
        re_path(r"^404/$", handler404),
        re_path(r"^500/$", handler500),
    ]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
