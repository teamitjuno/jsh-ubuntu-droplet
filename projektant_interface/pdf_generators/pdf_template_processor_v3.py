from fpdf import FPDF
import os, tempfile, fitz
from config import settings


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
        bauplan_img=None,
        bauplan_img_secondary=None,
        bauplan_img_third=None,
        font_size=18,
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
        self.bauplan_img_secondary = bauplan_img_secondary
        self.bauplan_img_third = bauplan_img_third
        self.font_size = font_size
        super().__init__("L", *args, **kwargs)

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

        self.multi_cell(col_width, row_height, item, border=0)

        self.set_font("JUNO Solar Lt", "", 9)
        self.set_xy(251, 182.5)
        item = f"{self.kunden_strasse}"

        self.multi_cell(col_width, row_height, item, border=0)

        self.set_font("JUNO Solar Lt", "", 9)
        self.set_xy(251, 186)
        item = f"{self.kunden_plz_ort}"

        self.multi_cell(col_width, row_height, item, border=0)

    def add_right_top_table(self, processed_besodersheiten):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)

        col_width = 80
        row_height = 6
        self.set_xy(214, 4)
        self.set_font("JUNO Solar Lt", "B", self.font_size)
        item = f"{processed_besodersheiten}"

        self.multi_cell(col_width, row_height, item, border=1)

    def add_right_top_table2(self, processed_besodersheiten):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)

        col_width = 111
        row_height = 6
        self.set_xy(183, 105)
        self.set_font("JUNO Solar Lt", "B", self.font_size)
        item = f"{processed_besodersheiten}"

        self.multi_cell(col_width, row_height, item, border=1)

    def add_right_top_table3(self, processed_besodersheiten):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)

        col_width = 152
        row_height = 6
        self.set_xy(143, 120)
        self.set_font("JUNO Solar Lt", "B", self.font_size)
        item = f"{processed_besodersheiten}"

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
        bauplan_img=data["bauplan_jpg_path"],
        bauplan_img_secondary=data["bauplan_jpg_secondary_path"],
        bauplan_img_third=data["bauplan_jpg_third_path"],
        font_size=data["font_size"],
    )

    img_paths = [
        (pdf.bauplan_img, 2, 4, 210, 167),
        (pdf.bauplan_img_secondary, 183, 4, 111, 100),
        (pdf.bauplan_img_third, 219, 4, 76, 115),
    ]

    if pdf.bauplan_img:
        pdf.add_page()
        if not pdf.bauplan_img_secondary and not pdf.bauplan_img_third:
            pdf.add_right_top_table(data["processed_besodersheiten"])
        elif not pdf.bauplan_img_third:
            pdf.add_right_top_table2(data["processed_besodersheiten"])
            img_paths[0] = (pdf.bauplan_img, 2, 4, 180, 167)
        else:
            pdf.add_right_top_table3(data["processed_besodersheiten"])
            img_paths[0] = (pdf.bauplan_img, 2, 4, 140, 167)
            img_paths[1] = (pdf.bauplan_img_secondary, 143, 4, 75, 115)

        for path, x, y, w, h in img_paths:
            if path:
                pdf.image(path, x=x, y=y, w=w, h=h)

        pdf.footer()

    return pdf.output(dest="S").encode("latin1")


def generate_pdf_bauplan(data):
    # Load the original template and the overlay content
    original = fitz.open("docs/template2.pdf")
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
