import os
import json
import logging
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from authentication.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import unquote
from django.http import (
    Http404,
    HttpResponseRedirect,
    JsonResponse,
    HttpResponse,
    FileResponse,
)
import re
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from shared.chat_bot import handle_message
from projektant_interface.pdf_generators.pdf_template_processor_v3 import (
    generate_pdf_bauplan,
    CustomPDF,
)
from projektant_interface.models import Project


def handler500(request):
    return render(request, "500.html", status=500)


def handler403(request, exception):
    return render(request, "403.html", status=403)


def handler404(request, exception):
    return render(request, "404.html", status=404)


def projektant_check(user):
    return User.objects.filter(id=user.id, beruf="Projektant").exists()


def extract_address_parts(my_str):
    pattern = r"^(.+?),\s+(.+)$"
    match = re.match(pattern, my_str)

    if match:
        kunden_strasse = match.group(1).strip()
        kunden_plz_ort = match.group(2).strip()
        return kunden_strasse, kunden_plz_ort
    else:
        return None, None


@user_passes_test(projektant_check)
def home(request):
    return render(request, "projektant/home.html")


class ProjektantCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return projektant_check(self.request.user)  # type: ignore


@user_passes_test(projektant_check)
def profile(request):
    user = request.user
    context = {"user": user}
    return render(request, "projektant/profile.html", context)


@user_passes_test(projektant_check)
def help(request):
    return render(request, "projektant/help.html")


@user_passes_test(projektant_check)
@csrf_exempt
def chat_bot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("question", "")
        response = handle_message(question)
        return JsonResponse({"response": response})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)


class ViewOrders(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projektant/view_orders.html"
    context_object_name = "projects"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.model.objects.filter(ID__regex=r"^\d+$")

        return queryset


@user_passes_test(projektant_check)
def create_project_bauplan_pdf(request, project_id):
    project = get_object_or_404(Project, ID=project_id)
    user = request.user
    processed_besodersheiten = project.Processed_Besonderheiten
    roof_typ = project.roof_typ
    height = project.height
    kunden_tel_nummer = project.Kunde_Telefon_mobil
    datetime = project.current_date
    user_surname = user.last_name
    kunden_name = project.kunden_name
    temp = project.temp_content_pdf
    kunden_strasse, kunden_plz_ort = extract_address_parts(
        str(project.Kunde_Adresse_PVA)
        if project.Kunde_Adresse_PVA
        else "Straße 0, Stadt, 00000"
    )
    # Sample data for demonstration
    data = {
        "roof_typ": roof_typ,
        "height": height,
        "kunden_tel_nummer": kunden_tel_nummer,
        "datetime": kunden_tel_nummer,
        "user_surname": user.last_name,
        "kunden_name": kunden_name,
        "kunden_strasse": kunden_strasse,
        "kunden_plz_ort": kunden_plz_ort,
        "processed_besodersheiten": processed_besodersheiten,
    }

    # Uncomment to use
    # result_pdf_content = overlay_on_template(data)
    pdf_content = generate_pdf_bauplan(data)
    project.bauplan_pdf = pdf_content
    project.save()

    return redirect("projektant_interface:document_view", project_id=project_id)


@user_passes_test(projektant_check)
def document_view(request, project_id):
    pdf_url = reverse("projektant_interface:serve_pdf", args=[project_id])
    context = {"pdf_url": pdf_url, "ID": project_id}
    return render(request, "projektant/document_view.html", context)


@user_passes_test(projektant_check)
def serve_pdf(request, project_id):
    decoded_project_id = unquote(str(project_id))
    project = get_object_or_404(Project, ID=decoded_project_id)
    filename = f"Lageplan_{project_id}.pdf"

    response = FileResponse(project.bauplan_pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"

    return response


# from django.http import FileResponse
# from config import settings

# def test_pdf_generation(request):
#     data = {
#         'roof_typ': project.roof_typ,
#         'height': project.height,
#         'kunden_tel_nummer': kunden_tel_nummer,
#         'datetime': kunden_tel_nummer,
#         'user_surname': user.last_name,
#         'kunden_name': project.kunden_name,
#         'kunden_strasse': kunden_strasse,
#         'kunden_plz_ort': kunden_plz_ort,
#         'processed_besodersheiten': processed_besodersheiten
#     }
#     pdf = CustomPDF(roof_typ=data['roof_typ'], height=data['height'],
#                 kunden_tel_nummer=data['kunden_tel_nummer'],
#                 datetime=data['datetime'], user_surname=data['user_surname'],
#                 kunden_name=data['kunden_name'], kunden_strasse=data['kunden_strasse'],
#                 kunden_plz_ort=data['kunden_plz_ort'])
#     font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
#     pdf.add_font("JUNO Solar Lt", "", font_path, uni=True)
#     font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
#     pdf.add_font("JUNO Solar Lt", "B", font_path, uni=True)
#     pdf.add_page()

#     # Set some dummy data for testing
#     pdf.roof_typ = "Test Roof"
#     pdf.height = "10m"
#     pdf.kunden_tel_nummer = "+1234567890"
#     pdf.datetime = "2023-08-11"
#     pdf.user_surname = "Doe"
#     pdf.kunden_name = "John"
#     pdf.kunden_strasse = "123 Test St."
#     pdf.kunden_plz_ort = "Test City, 12345"

#     # Call the content methods
#     pdf.footer()
#     pdf.add_right_top_table("Test Data")

#     # Generate the PDF and return as a response
#     response = FileResponse(pdf.output(dest='S').encode('latin-1'))
#     response['Content-Type'] = 'application/pdf'
#     response['Content-Disposition'] = 'inline; filename="test.pdf"'

#     return response
