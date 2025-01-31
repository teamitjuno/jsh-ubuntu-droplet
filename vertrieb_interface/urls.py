from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from vertrieb_interface.api_views import views
from vertrieb_interface.api_views.angebot_main_view import AngebotEditView
from vertrieb_interface.api_views.ticket_main_view import TicketNewEditView
from vertrieb_interface.api_views.kalkulation_view import KalkulationEditView
from vertrieb_interface.api_views.auto_field_view import VertriebAutoFieldView
from vertrieb_interface.api_views.alle_angebote_view import ViewOrders
from vertrieb_interface.api_views.alle_tickets_view import ViewOrdersTicket
from vertrieb_interface.api_views.document_PDF_view import DocumentView
from vertrieb_interface.api_views.document_ticket_PDF_view import DocumentViewTicket
from vertrieb_interface.api_views.document_ticket_new_PDF_view import DocumentViewTicketNew
from vertrieb_interface.api_views.document_and_calculation_PDF_view import (
    DocumentAndCalcView,
)

from django.views import defaults as default_views
from adminfeautures.views import UpdateAdminAngebot

app_name = "vertrieb_interface"

# Vertrieb URLs
vertrieb_patterns = [
    path("vertrieb/home/", views.home, name="home"),
    path("vertrieb/user_redirect", views.user_redirect_view, name="user_redirect"),
    path(
        "vertrieb/home/reset_calculator/",
        views.reset_calculator,
        name="reset_calculator",
    ),
    path(
        "vertrieb/edit_angebot/map/<str:angebot_id>/", views.map_view, name="map_view"
    ),
path(
        "vertrieb/edit_ticket_new/map/<str:ticket_id>/", views.map_view, name="map_view"
    ),
    path(
        "vertrieb/vertrieb_autofield/",
        VertriebAutoFieldView.as_view(),
        name="vertrieb_autofield",
    ),
    path("vertrieb/create_angebot/", views.create_angebot, name="create_angebot"),
    path("vertrieb/create_ticket_new/", views.create_ticket_new, name="create_ticket_new"),
    path(
        "vertrieb/create_angebot_redirect/",
        views.create_angebot_redirect,
        name="create_angebot_redirect",
    ),
    path("vertrieb/help/", views.help, name="help"),
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
    path("vertrieb/view_orders/", ViewOrders.as_view(), name="view_orders"),
    path(
        "vertrieb/view_orders/delete/<str:angebot_id>/",
        views.DeleteUserAngebot.as_view(),
        name="delete_user_angebot",
    ),
    path("vertrieb/view_orders_ticket/", ViewOrdersTicket.as_view(), name="view_orders_ticket"),
    path(
        "vertrieb/view_orders_ticket/delete/<str:ticket_id>/",
        views.DeleteUserTicket.as_view(),
        name="delete_user_ticket_new",
    ),
    path(
        "vertrieb/edit_angebot/<str:angebot_id>/",
        AngebotEditView.as_view(),
        name="edit_angebot",
    ),
path(
        "vertrieb/edit_ticket_new/<str:ticket_id>/",
        TicketNewEditView.as_view(),
        name="edit_ticket_new",
    ),
    path(
        "vertrieb/edit_calc/<str:angebot_id>/",
        KalkulationEditView.as_view(),
        name="edit_calc",
    ),
    path(
        "vertrieb/update_admin_angebot/<str:angebot_id>/",
        UpdateAdminAngebot.as_view(),
        name="update_admin_angebot",
    ),
    path(
        "vertrieb/create_angebot_pdf_user/<str:angebot_id>",
        views.create_angebot_pdf_user,
        name="create_angebot_pdf_user",
    ),
    path(
        "vertrieb/create_ticket_new_pdf_user/<str:ticket_id>",
        views.create_ticket_new_pdf_user,
        name="create_ticket_new_pdf_user",
    ),
    path(
        "vertrieb/create_calc_pdf/<str:angebot_id>",
        views.create_calc_pdf,
        name="create_calc_pdf",
    ),
    path(
        "vertrieb/create_angebot_and_calc_pdf/<str:angebot_id>",
        views.create_angebot_and_calc_pdf,
        name="create_angebot_and_calc_pdf",
    ),
    path(
        "update_vertrieb_angebot/<int:angebot_id>/",
        views.UpdateVertriebAngebotView.as_view(),
        name="update_vertrieb_angebot",
    ),
    path(
        "vertrieb/pdf_angebots_list_view/",
        views.PDFAngebotsListView.as_view(),
        name="pdf_angebots_list_view",
    ),
path(
        "vertrieb/pdf_tickets_list_view/",
        views.PDFTicketsListView.as_view(),
        name="pdf_tickets_list_view",
    ),
    path(
        "PDFCalculationsListView/<str:angebot_id>/",
        views.PDFCalculationsListView,
        name="PDFCalculationsListView",
    ),
    path(
        "PDFTicketListView/<str:angebot_id>/",
        views.pdfticket_list_view,
        name="PDFTicketListView",
    ),
    path("serve_pdf/<str:angebot_id>/", views.serve_pdf, name="serve_pdf"),
    path(
        "serve_calc_pdf/<str:angebot_id>/", views.serve_calc_pdf, name="serve_calc_pdf"
    ),
    path(
        "serve_ticket_new_pdf/<str:ticket_id>/",
        views.serve_ticket_new_pdf,
        name="serve_ticket_new_pdf",
    ),
    path("document/<str:angebot_id>/", DocumentView.as_view(), name="document_view"),
    path("documentTicket/<str:ticket_id>/", DocumentViewTicket.as_view(), name="document_view_ticket"),
    path("documentTicketNew/<str:ticket_id>/", DocumentViewTicketNew.as_view(), name="document_view_ticket_new"),
    path(
        "document_calc/<str:angebot_id>/",
        views.document_calc_view,
        name="document_calc_view",
    ),
    path(
        "document_and_calc_view/<str:angebot_id>/",
        DocumentAndCalcView.as_view(),
        name="document_and_calc_view",
    ),
    path("serve_dokumentation/", views.serve_dokumentation, name="serve_dokumentation"),
    path("documentation_view/", views.documentation_view, name="documentation_view"),
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
    path("vertrieb/intermediate/", views.intermediate_view, name="intermediate_view"),
]

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
