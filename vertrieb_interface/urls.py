from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from vertrieb_interface import views
from django.views import defaults as default_views
from adminfeautures.views import UpdateAdminAngebot

app_name = "vertrieb_interface"

# Vertrieb URLs
vertrieb_patterns = [
    path("vertrieb/home/", views.home, name="home"),
    path(
        "vertrieb/home/reset_calculator/",
        views.reset_calculator,
        name="reset_calculator",
    ),
    path(
        "vertrieb/edit_angebot/map/<str:angebot_id>/", views.map_view, name="map_view"
    ),
    path(
        "vertrieb/vertrieb_autofield/",
        views.VertriebAutoFieldView.as_view(),
        name="vertrieb_autofield",
    ),
    path("vertrieb/create_angebot/", views.create_angebot, name="create_angebot"),
    path("vertrieb/help/", views.help, name="help"),
    path("vertrieb/chat_bot/", views.chat_bot, name="chat_bot"),
    path(
        "vertrieb/calc_graph_display/",
        views.calc_graph_display,
        name="calc_graph_display",
    ),
    path("vertrieb/get_data/", views.get_data, name="get_data"),
    path(
        "vertrieb/load_user_angebots/",
        views.load_user_angebots,
        name="load_user_angebots",
    ),
    path("vertrieb/profile/", views.profile, name="profile"),
    path("vertrieb/view_orders/", views.ViewOrders.as_view(), name="view_orders"),
    path(
        "vertrieb/ticket_creation/",
        views.TicketCreationView.as_view(),
        name="ticket_creation",
    ),
    path(
        "vertrieb/edit_angebot/<str:angebot_id>/",
        views.AngebotEditView.as_view(),
        name="edit_angebot",
    ),
    path(
        "vertrieb/edit_ticket/<str:angebot_id>/",
        views.TicketEditView.as_view(),
        name="edit_ticket",
    ),
    path(
        "vertrieb/update_admin_angebot/<str:angebot_id>/",
        UpdateAdminAngebot.as_view(),
        name="update_admin_angebot",
    ),
    path(
        "vertrieb/create_angebot_pdf/<str:angebot_id>",
        views.create_angebot_pdf,
        name="create_angebot_pdf",
    ),
    path(
        "vertrieb/create_angebot_pdf_user/<str:angebot_id>",
        views.create_angebot_pdf_user,
        name="create_angebot_pdf_user",
    ),
    path(
        "vertrieb/create_ticket_pdf/<str:angebot_id>",
        views.create_ticket_pdf,
        name="create_ticket_pdf",
    ),
    path(
        "vertrieb/create_calc_pdf/<str:angebot_id>",
        views.create_calc_pdf,
        name="create_calc_pdf",
    ),
    path(
        "update_vertrieb_angebot/<int:angebot_id>/",
        views.UpdateVertriebAngebotView.as_view(),
        name="update_vertrieb_angebot",
    ),
    path(
        "vertrieb/pdf_angebots_list_view/",
        views.pdf_angebots_list_view,
        name="pdf_angebots_list_view",
    ),
    path(
        "PDFCalculationsListView/<str:angebot_id>/",
        views.PDFCalculationsListView,
        name="PDFCalculationsListView",
    ),
    path(
        "PDFTicketListView/<str:angebot_id>/",
        views.PDFTicketListView,
        name="PDFTicketListView",
    ),
    path("serve_pdf/<str:angebot_id>/", views.serve_pdf, name="serve_pdf"),
    path(
        "serve_calc_pdf/<str:angebot_id>/", views.serve_calc_pdf, name="serve_calc_pdf"
    ),
    path(
        "serve_ticket_pdf/<str:angebot_id>/",
        views.serve_ticket_pdf,
        name="serve_ticket_pdf",
    ),
    path("document/<str:angebot_id>/", views.document_view, name="document_view"),
    path(
        "document_calc/<str:angebot_id>/",
        views.document_calc_view,
        name="document_calc_view",
    ),
    path(
        "document_ticket/<str:angebot_id>/",
        views.document_ticket_view,
        name="document_ticket_view",
    ),
    path("send_invoice/<str:angebot_id>/", views.send_invoice, name="send_invoice"),
    path(
        "vertrieb/send_support_message/",
        views.send_support_message,
        name="send_support_message",
    ),
    path(
        "send_calc_invoice/<str:angebot_id>/",
        views.send_calc_invoice,
        name="send_calc_invoice",
    ),
    path(
        "send_ticket_invoice/<str:angebot_id>/",
        views.send_ticket_invoice,
        name="send_ticket_invoice",
    ),
]

# Error Handlers
error_patterns = [
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

urlpatterns = vertrieb_patterns + error_patterns
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
