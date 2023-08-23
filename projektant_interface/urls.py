from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from projektant_interface import views
from invoices.views import handler404, handler403, handler500


app_name = "projektant_interface"

urlpatterns = [
    path("home/", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("help/", views.help, name="help"),
    path("chat_bot/", views.chat_bot, name="chat_bot"),
    path("view_orders/", views.ViewOrders.as_view(), name="view_orders"),
    path(
        "create_bauplan_pdf/<int:project_id>/",
        views.create_project_bauplan_pdf,
        name="create_bauplan_pdf",
    ),
    path("document_view/<int:project_id>/", views.document_view, name="document_view"),
    path("serve_pdf/<int:project_id>/", views.serve_pdf, name="serve_pdf"),
    # path('test_pdf/', views.test_pdf_generation, name='test_pdf_generation'),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
