from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from projektant_interface import views

app_name = "projektant_interface"

urlpatterns = [
    path("home/", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("help/", views.help, name="help"),
    path("populate_projects/", views.populate_projects_view, name="populate_projects"),
    path("view_orders/", views.ViewOrders.as_view(), name="view_orders"),
    path(
        "create_bauplan_pdf/<int:project_id>/",
        views.create_project_bauplan_pdf,
        name="create_bauplan_pdf",
    ),
    path("document_view/<int:project_id>/", views.document_view, name="document_view"),
    path("send_invoice/", views.send_invoice, name="send_invoice"),
    path("serve_pdf/<int:project_id>/", views.serve_pdf, name="serve_pdf"),
    path(
        "project/<int:project_id>/upload_jpg/", views.upload_jpg, name="upload_jpg"
    ),  # New URL pattern for JPG upload
    path(
        "project/<int:project_id>/update/", views.update_project, name="update_project"
    ),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
