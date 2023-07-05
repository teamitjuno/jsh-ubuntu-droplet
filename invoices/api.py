from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .serializers import (
    ElectricInvoiceSerializer,
    KundenDataSerializer,
    PositionSerializer,
)
from .models import ElectricInvoice, KundenData, Position
from .forms import KundenDataForm
from . import pdf_creator2
from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import (
    ElectricInvoiceSerializer,
    KundenDataSerializer,
    PositionSerializer,
)
from .models import ElectricInvoice, KundenData, Position
from .forms import KundenDataForm
from authentication.models import User
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, HttpResponseRedirect


# User's profession check decorators
def elektriker_check(user):
    return User.objects.filter(id=user.id, beruf="Elektriker").exists()


def verkaufer_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class ElektrikerCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return elektriker_check(self.request.user)  # type: ignore


class ElectricInvoiceViewSet(viewsets.ModelViewSet):
    queryset = ElectricInvoice.objects.all()
    serializer_class = ElectricInvoiceSerializer


class KundenDataViewSet(viewsets.ModelViewSet):
    queryset = KundenData.objects.all()
    serializer_class = KundenDataSerializer


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer


@api_view(["PUT"])
def update_kunden_data(request_data, invoice_id):
    invoice = get_object_or_404(ElectricInvoice, invoice_id=invoice_id)
    kunden_data = getattr(invoice, "kunden_data", None)

    if kunden_data is not None:
        form = KundenDataForm(request_data, instance=kunden_data)
    else:
        form = KundenDataForm(request_data)

    if form.is_valid():
        kunden_data = form.save(commit=False)
        if kunden_data.invoice_id is None:
            kunden_data.invoice = invoice
        kunden_data.save()
        invoice.is_locked = True
        invoice.save()
        return True
    else:
        return form.errors


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 22
    page_size_query_param = "page_size"
    max_page_size = 1000


class ViewOrders(ElektrikerCheckMixin, generics.ListAPIView):
    model = ElectricInvoice
    serializer_class = ElectricInvoiceSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        invoice_id_regex = r"^.*$"
        queryset = self.model.objects.filter(
            user=user, invoice_id__regex=invoice_id_regex
        )

        query = self.request.query_params.get("q")  # type: ignore
        if query:
            queryset = queryset.filter(Q(invoice_id__icontains=query))

        return queryset


@api_view(["GET"])
def get_orders(request):
    invoices = list(ElectricInvoice.objects.values())
    return Response(invoices)


@api_view(["POST"])
def create_pdf(request, invoice_id):
    invoice = get_object_or_404(ElectricInvoice, invoice_id=invoice_id)
    user = invoice.user
    if request.user != invoice.user and not request.user.is_staff:
        raise Http404("Permission denied.")
    mats = Position.objects.filter(invoice=invoice)
    k_data = KundenData.objects.filter(invoice=invoice)
    eintrag = 0
    pdf_creator2.createOfferPdf(
        invoice,
        eintrag,
        user,
        mats,
        k_data,
    )
    # Create the link to the PDF file
    pdf_link = os.path.join(settings.MEDIA_URL, f"pdf/usersangebots/{user.username}/Angebot_{invoice.invoice_id}.pdf")  # type: ignore

    # Redirect to the PDF file link
    return HttpResponseRedirect(pdf_link)


from rest_framework import mixins

# class EditInvoiceView(ElektrikerCheckMixin, mixins.UpdateModelMixin, generics.RetrieveAPIView):
#     model = ElectricInvoice
#     form_class = KundenDataForm
#     serializer_class = ElectricInvoiceSerializer

#     def get_object(self):
#         invoice_id = self.kwargs.get("invoice_id")
#         return get_object_or_404(ElectricInvoice, invoice_id=invoice_id)

#     def put(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         if "delete_position" in request.POST:
#             return self.delete_position(request)
#         elif "uss" in request.POST:
#             return self.add_uss(request)
#         elif "sls" in request.POST:
#             return self.add_sls(request)
#         elif "b_material" in request.POST:
#             return self.add_b_material(request)
#         elif "leitungschutzschalter" in request.POST:
#             return self.add_leitungschutzschalter(request)
#         elif "hauptabzweigklemme" in request.POST:
#             return self.add_hauptabzweigklemme(request)
#         elif "mantelleitung" in request.POST:
#             return self.add_mantelleitung(request)
#         elif "kabelkanal" in request.POST:
#             return self.add_kabelkanal(request)
#         elif "zahler_kabel" in request.POST:
#             return self.add_zahler_kabel(request)
#         elif "kunden_data" in request.POST:
#             return self.update_kunden_data(request)


@api_view(["GET"])
def PDFInvoicesListView(request, invoice_id):
    invoice = get_object_or_404(ElectricInvoice, invoice_id=invoice_id)
    user = invoice.user
    ...


@api_view(["POST"])
def create_excel(request, invoice_id):
    ...


@api_view(["GET"])
def EXCELInvoicesListView(request, invoice_id):
    invoice = get_object_or_404(ElectricInvoice, invoice_id=invoice_id)
    user = invoice.user
    ...
