from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter
import os
import io
import tempfile
from config import settings
from fpdf import FPDF
import fitz
import os


class CustomPDF(FPDF):
    def __init__(
        self,
        *args,
        roof_typ=None,
        height=None,
        kunden_tel_nummer=None,
        datetime="30.08.23",
        user_surname="",
        kunden_name="Hui Nahui",
        kunden_strasse="",
        kunden_plz_ort="",
        bauplan_img = None,
        **kwargs,
    ):
        self.roof_typ = roof_typ
        self.height = height
        self.kunden_tel_nummer = kunden_tel_nummer
        self.datetime = datetime
        self.user_surname = user_surname
        self.kunden_name = kunden_name
        self.kunden_strasse = kunden_strasse
        self.kunden_plz_ort = kunden_plz_ort
        self.bauplan_img = bauplan_img
        super().__init__('L', *args, **kwargs)


    def footer(self):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)
        col_width = 55
        row_height = 6
        self.set_xy(67, 181.5)
        self.set_font("JUNO Solar Lt", "", 14)
        item = f"{self.roof_typ}"
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_xy(67, 187.7)
        self.set_font("JUNO Solar Lt", "", 14)
        item = f"{self.height}"
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_xy(67, 194.5)
        self.set_font("JUNO Solar Lt", "", 14)
        item = f"{self.kunden_tel_nummer}"
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_font("JUNO Solar Lt", "", 9)
        self.set_xy(187, 181)
        item = f"{self.datetime}"
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_font("JUNO Solar Lt", "", 9)
        self.set_xy(206, 181)
        item = f"{self.user_surname}"
        self.multi_cell(col_width, row_height, item, border=0)

        col_width = 290
        row_height = 8
        
        self.set_xy(251, 179)
        self.set_font("JUNO Solar Lt", "", 9)
        item = f"{self.kunden_name}"
        print(item)
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_font("JUNO Solar Lt", "", 9)
        self.set_xy(251, 182.5)
        item = f"{self.kunden_strasse}"
        print(item)
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_font("JUNO Solar Lt", "", 9)
        self.set_xy(251, 186)
        item = f"{self.kunden_plz_ort}"
        print(item)
        self.multi_cell(col_width, row_height, item, border=0)

    def add_right_top_table(self, processed_besodersheiten):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)
        
        col_width = 80
        row_height = 6
        self.set_xy(214, 5)
        self.set_font("JUNO Solar Lt", "B", 16)
        item = f'{processed_besodersheiten}'
        print(item)
        self.multi_cell(col_width, row_height, item, border=1)


def generate_overlay_pdf(data):
    pdf = CustomPDF(
        roof_typ=data["roof_typ"],
        height=data["height"],
        kunden_tel_nummer=data["kunden_tel_nummer"],
        datetime=data["datetime"],
        user_surname=data["user_surname"],
        kunden_name=data["kunden_name"],
        kunden_strasse=data["kunden_strasse"],
        kunden_plz_ort=data["kunden_plz_ort"],
        bauplan_img = data["bauplan_jpg_path"],
    )
    pdf.add_page()
    pdf.add_right_top_table(data["processed_besodersheiten"])
    pdf.footer()  # Note: No arguments here now
    if pdf.bauplan_img:
        img_path = pdf.bauplan_img
        pdf.image(img_path, x=10, y=20, w=190)
    
    return pdf.output(dest="S").encode("latin1")


def generate_pdf_bauplan(data):
    # Load the original template and the overlay content
    original = fitz.open("template2.pdf")
    overlay_pdf_content = generate_overlay_pdf(data)
    overlay = fitz.open("pdf", overlay_pdf_content)

    # Overlay the pages
    page = original[0]
    page.show_pdf_page(page.rect, overlay, 0)

    # Save the combined content to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=True)
    original.save(temp_file.name)

    # Read the contents of the temporary file
    with open(temp_file.name, "rb") as f:
        pdf_content = f.read()

    # Return the combined content
    return pdf_content


# def generate_pdf_bauplan(project_id, temp, processed_besodersheiten, roof_typ, height, kunden_tel_nummer, datetime, user_surname, kunden_name, kunden_strasse, kunden_plz_ort):
#     # Create a temporary PDF with the new content
#     title = f"Lageplan_{project_id}"
#     overlay = CustomPDF(orientation='landscape')
#     overlay.roof_typ = roof_typ
#     overlay.height = height
#     overlay.kunden_tel_nummer = kunden_tel_nummer
#     overlay.datetime = datetime
#     overlay.user_surname = user_surname
#     overlay.kunden_name = kunden_name
#     overlay.kunden_strasse = kunden_strasse
#     overlay.kunden_plz_ort = kunden_plz_ort
#     overlay.temp = temp
#     # Adjusted font paths and added them to the FPDF instance
#     font_path_regular = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
#     overlay.add_font("JUNO Solar Lt", "", font_path_regular, uni=True)
#     font_path_bold = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
#     overlay.set_title(title)
#     overlay.set_author("JUNO Solar Home GmbH")

#     overlay.add_page()

#     overlay.add_font("JUNO Solar Lt", "B", font_path_bold, uni=True)
#     overlay.set_font("JUNO Solar Lt", "", 12)
#     overlay.set_text_color(0)

#     overlay.header()

#     overlay.add_right_top_table(processed_besodersheiten)

#     overlay.footer()

#     temp_output_path = os.path.join(settings.MEDIA_ROOT, "fonts/temp_content.pdf")
#     overlay.temp = overlay.output(dest="S").encode("latin1")


#     # Overlay the new content on the existing 'template.pdf'
#     original = PdfReader(os.path.join(settings.STATIC_ROOT, "fonts/template2.pdf"))
#     byte_data = overlay.temp
#     file_like_object = io.BytesIO(byte_data)
#     overlay_pdf = PdfReader(file_like_object)
#     writer = PdfWriter()

#     # Take the page from the original PDF and merge it with the overlay PDF
#     page = original.pages[0]
#     page.merge_page(overlay_pdf.pages[0])


#     pdf_content = overlay.output(dest="S").encode("latin1")
#     return pdf_content



# I have a django project, and I have a pdf generation function: 

# class CustomPDF(FPDF):
#     def __init__(
#         self,
#         *args,
#         roof_typ=None,
#         height=None,
#         kunden_tel_nummer=None,
#         datetime="30.08.23",
#         user_surname="",
#         kunden_name="Hui Nahui",
#         kunden_strasse="",
#         kunden_plz_ort="",
#         **kwargs,
#     ):
#         self.roof_typ = roof_typ
#         self.height = height
#         self.kunden_tel_nummer = kunden_tel_nummer
#         self.datetime = datetime
#         self.user_surname = user_surname
#         self.kunden_name = kunden_name
#         self.kunden_strasse = kunden_strasse
#         self.kunden_plz_ort = kunden_plz_ort
#         super().__init__('L', *args, **kwargs)


#     def footer(self):
#         font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
#         self.add_font("JUNO Solar Lt", "", font_path, uni=True)
#         font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
#         self.add_font("JUNO Solar Lt", "B", font_path, uni=True)
#         col_width = 55
#         row_height = 6
#         self.set_xy(67, 181.5)
#         self.set_font("JUNO Solar Lt", "", 14)
#         item = f"{self.roof_typ}"
#         self.multi_cell(col_width, row_height, item, border=0)

#         self.set_xy(67, 187.7)
#         self.set_font("JUNO Solar Lt", "", 14)
#         item = f"{self.height}"
#         self.multi_cell(col_width, row_height, item, border=0)

#         self.set_xy(67, 194.5)
#         self.set_font("JUNO Solar Lt", "", 14)
#         item = f"{self.kunden_tel_nummer}"
#         self.multi_cell(col_width, row_height, item, border=0)

#         self.set_font("JUNO Solar Lt", "", 9)
#         self.set_xy(187, 181)
#         item = f"{self.datetime}"
#         self.multi_cell(col_width, row_height, item, border=0)

#         self.set_font("JUNO Solar Lt", "", 9)
#         self.set_xy(206, 181)
#         item = f"{self.user_surname}"
#         self.multi_cell(col_width, row_height, item, border=0)

#         col_width = 290
#         row_height = 8
        
#         self.set_xy(251, 179)
#         self.set_font("JUNO Solar Lt", "", 9)
#         item = f"{self.kunden_name}"
#         print(item)
#         self.multi_cell(col_width, row_height, item, border=0)

#         self.set_font("JUNO Solar Lt", "", 9)
#         self.set_xy(251, 182.5)
#         item = f"{self.kunden_strasse}"
#         print(item)
#         self.multi_cell(col_width, row_height, item, border=0)

#         self.set_font("JUNO Solar Lt", "", 9)
#         self.set_xy(251, 186)
#         item = f"{self.kunden_plz_ort}"
#         print(item)
#         self.multi_cell(col_width, row_height, item, border=0)

#     def add_right_top_table(self, processed_besodersheiten):
#         font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
#         self.add_font("JUNO Solar Lt", "", font_path, uni=True)
#         font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
#         self.add_font("JUNO Solar Lt", "B", font_path, uni=True)
        
#         col_width = 80
#         row_height = 6
#         self.set_xy(214, 5)
#         self.set_font("JUNO Solar Lt", "B", 16)
#         item = f'{processed_besodersheiten}'
#         print(item)
#         self.multi_cell(col_width, row_height, item, border=1)


# def generate_overlay_pdf(data):
#     pdf = CustomPDF(
#         roof_typ=data["roof_typ"],
#         height=data["height"],
#         kunden_tel_nummer=data["kunden_tel_nummer"],
#         datetime=data["datetime"],
#         user_surname=data["user_surname"],
#         kunden_name=data["kunden_name"],
#         kunden_strasse=data["kunden_strasse"],
#         kunden_plz_ort=data["kunden_plz_ort"],
#     )
#     pdf.add_page()
#     pdf.add_right_top_table(data["processed_besodersheiten"])
#     pdf.footer()  # Note: No arguments here now
    
#     return pdf.output(dest="S").encode("latin1")


# def generate_pdf_bauplan(data):
#     # Load the original template and the overlay content
#     original = fitz.open("template2.pdf")
#     overlay_pdf_content = generate_overlay_pdf(data)
#     overlay = fitz.open("pdf", overlay_pdf_content)

#     # Overlay the pages
#     page = original[0]
#     page.show_pdf_page(page.rect, overlay, 0)

#     # Save the combined content to a temporary file
#     temp_file = tempfile.NamedTemporaryFile(delete=True)
#     original.save(temp_file.name)

#     # Read the contents of the temporary file
#     with open(temp_file.name, "rb") as f:
#         pdf_content = f.read()

#     # Return the combined content
#     return pdf_content

# views.py:

# @user_passes_test(projektant_check)
# def create_project_bauplan_pdf(request, project_id):
#     project = get_object_or_404(Project, ID=project_id)
#     user = request.user
#     processed_besodersheiten = project.Processed_Besonderheiten
#     roof_typ = project.roof_typ
#     height = project.height
#     kunden_tel_nummer = project.Kunde_Telefon_mobil
#     datetime = project.current_date
#     user_surname = user.last_name
#     kunden_name = project.kunden_name
#     temp = project.temp_content_pdf
#     kunden_strasse, kunden_plz_ort = extract_address_parts(
#         str(project.Kunde_Adresse_PVA)
#         if project.Kunde_Adresse_PVA
#         else "Straße 0, Stadt, 00000"
#     )
#     # Sample data for demonstration
#     data = {
#         "roof_typ": roof_typ,
#         "height": height,
#         "kunden_tel_nummer": kunden_tel_nummer,
#         "datetime": datetime,
#         "user_surname": user_surname,
#         "kunden_name": kunden_name,
#         "kunden_strasse": kunden_strasse,
#         "kunden_plz_ort": kunden_plz_ort,
#         "processed_besodersheiten": processed_besodersheiten,
#     }

#     # Uncomment to use
#     # result_pdf_content = overlay_on_template(data)
#     pdf_content = generate_pdf_bauplan(data)
#     project.bauplan_pdf = pdf_content
#     project.save()

#     return redirect("projektant_interface:document_view", project_id=project_id)


# @user_passes_test(projektant_check)
# def document_view(request, project_id):
#     pdf_url = reverse("projektant_interface:serve_pdf", args=[project_id])
#     context = {"pdf_url": pdf_url, "ID": project_id}
#     return render(request, "projektant/document_view.html", context)


# @user_passes_test(projektant_check)
# def serve_pdf(request, project_id):
#     decoded_project_id = unquote(str(project_id))
#     project = get_object_or_404(Project, ID=decoded_project_id)
#     filename = f"Lageplan_{project_id}.pdf"

#     response = FileResponse(project.bauplan_pdf, content_type="application/pdf")
#     response["Content-Disposition"] = f"inline; filename={filename}"

#     return response


# I want to implement for a user -  a file upload form field for jpg file. And this file must be saved to the 
# class Project(models.Model):
# bauplan_jpg = models.ImageField(null=True, blank=True)
# Also this jpg must be placed on my pdf document during pdf generation