from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter
import os


class CustomPDF(FPDF):
    def header(self):
        pass

    def add_left_bottom_text(self):
        col_width = 38
        row_height = 5
        self.set_xy(85, 170)

        self.set_font("JUNO Solar Lt", "B", 11)
        item = "ROOF TYP\nHEIGHT\nproject.Kunde_Telefon_mobil"
        self.multi_cell(col_width, row_height, item, border=1)

    def add_right_top_table(self):
        self.set_font("JUNO Solar Lt", "B", 13)
        col_width = 58
        row_height = 5
        self.set_xy(211, 25)
        item = "project Processed_Besonderheiten dasdasda project. Kunde_Telefon _mobil project. Kunde_Telefon_ mobil project. Kunde_Telefon_ mobil \n Kunde_Telefon_ mobil \n\nKunde_Telefon_ mobil"
        self.multi_cell(col_width, row_height, item, border=1)

    def add_right_bottom_table(pdf):
        table_bottom_right_x = 180
        table_bottom_right_y = 80


def create_pdf():
    # Create a temporary PDF with the new content
    overlay = CustomPDF(orientation="L")
    overlay.add_page()

    # Adjusted font paths and added them to the FPDF instance
    font_path_regular = os.path.join("static", "fonts/JUNOSolarLt.ttf")
    overlay.add_font("JUNO Solar Lt", "", font_path_regular, uni=True)
    font_path_bold = os.path.join("static", "fonts/JUNOSolarRg.ttf")
    overlay.add_font("JUNO Solar Lt", "B", font_path_bold, uni=True)
    overlay.set_font("JUNO Solar Lt", "", 12)
    overlay.set_text_color(0)

    overlay.add_left_bottom_text()
    overlay.add_right_top_table()
    overlay.add_right_bottom_table()

    temp_output_path = "docs/temp_content.pdf"
    overlay.output(temp_output_path)

    # Overlay the new content on the existing 'template.pdf'
    original = PdfReader("docs/template2.pdf")
    overlay_pdf = PdfReader(temp_output_path)
    writer = PdfWriter()

    # Take the page from the original PDF and merge it with the overlay PDF
    page = original.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    final_output_path = "generated_processed_template.pdf"
    with open(final_output_path, "wb") as output_file_handle:
        writer.write(output_file_handle)
    print(f"PDF saved to {final_output_path}")


if __name__ == "__main__":
    create_pdf()
