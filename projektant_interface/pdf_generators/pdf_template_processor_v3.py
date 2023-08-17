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

    def __init__(self, *args, roof_typ=None, height=None, kunden_tel_nummer=None, datetime=None, 
            user_surname=None, kunden_name=None, kunden_strasse=None, kunden_plz_ort=None, **kwargs):
        self.roof_typ = roof_typ
        self.height = height
        self.kunden_tel_nummer = kunden_tel_nummer
        self.datetime = datetime
        self.user_surname = user_surname
        self.kunden_name = kunden_name
        self.kunden_strasse = kunden_strasse
        self.kunden_plz_ort = kunden_plz_ort
        super().__init__(*args, **kwargs)

    def footer(self):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)
        col_width = 55
        row_height = 6
        self.set_xy(0, 258)
        self.set_font("JUNO Solar Lt", "", 18)
        item = f"{self.roof_typ}"
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_xy(0, 267)
        self.set_font("JUNO Solar Lt", "", 18)
        item = f"{self.height}"
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_xy(0, 277)
        self.set_font("JUNO Solar Lt", "", 18)
        item = f"{self.kunden_tel_nummer}"
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_font("JUNO Solar Lt", "", 9)
        self.set_xy(173, 258)
        item = str(self.datetime)
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_xy(190, 258)
        item = str(self.user_surname)    
        self.multi_cell(col_width, row_height, item, border=0)

        row_height = 5
        self.set_xy(231, 258)
        item = str(self.kunden_name)
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_xy(231, 268)
        item = str(self.kunden_strasse)
        self.multi_cell(col_width, row_height, item, border=0)

        self.set_xy(231, 189)
        item = str(self.kunden_plz_ort)
        self.multi_cell(col_width, row_height, item, border=0)

    def add_right_top_table(self, processed_besodersheiten):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)
        self.set_font("JUNO Solar Lt", "B", 13)
        col_width = 38
        row_height = 5
        self.set_xy(230, 25)
        item = str(processed_besodersheiten)
        self.multi_cell(col_width, row_height, item, border=1)


def generate_overlay_pdf(data):
    pdf = CustomPDF(roof_typ=data['roof_typ'], height=data['height'], 
                kunden_tel_nummer=data['kunden_tel_nummer'], 
                datetime=data['datetime'], user_surname=data['user_surname'], 
                kunden_name=data['kunden_name'], kunden_strasse=data['kunden_strasse'], 
                kunden_plz_ort=data['kunden_plz_ort'])
    pdf.add_page()
    pdf.footer()  # Note: No arguments here now
    pdf.add_right_top_table(data['processed_besodersheiten'])
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
    with open(temp_file.name, 'rb') as f:
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