from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from invoices import views


app_name = "invoices"

urlpatterns = [
    path("home/", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("view_orders/", views.ViewOrders.as_view(), name="view_orders"),
    path("help/", views.help, name="help"),
    path("create_invoice/", views.create_invoice, name="create_invoice"),
    path("api/sync_data", views.sync_data, name="sync_data"),
    path(
        "edit_invoice/<str:invoice_id>/",
        views.EditInvoiceView.as_view(),
        name="edit_invoice",
    ),
    path("create_pdf/<invoice_id>", views.create_pdf, name="create_pdf"),
    path("create_xlsx/<invoice_id>'/", views.create_excel, name="create_excel"),
    path("process_files/", views.ProcessFilesView.as_view(), name="process_files"),
    path("tom/", views.tom, name="tom"),
    path(
        "pdf_invoices_list/",
        views.PDFInvoicesListViewCBV.as_view(),
        name="pdf_invoices_list",
    ),
    path(
        "xlsx_invoices_list/",
        views.EXCELInvoicesListViewCBV.as_view(),
        name="excel_invoices_list",
    ),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
