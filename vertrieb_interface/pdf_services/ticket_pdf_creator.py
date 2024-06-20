from config import settings
from math import ceil
from datetime import datetime, date
from vertrieb_interface.pdf_services.helper_functions import convertCurrency
from vertrieb_interface.models import Editierbarer_Text
from fpdf import FPDF
import os


title = ""
pages = 4


class PDF(FPDF):
    def __init__(self, title1, *args, **kwargs):
        """
        Initialisiert das PDF-Objekt mit spezifischen Margen und Linienbreiten.
        """
        super(PDF, self).__init__(*args, **kwargs)
        self.is_last_page = False
        self.title1 = title1
        self.set_left_margin(18.875)
        self.set_right_margin(12.875)
        self.set_line_width(0.5)


    def get_attribute_by_identifier(self, identifier, attribute):
        """
        Ruft ein Attribut eines editierbaren Textes ab, wobei Standardwerte zurückgegeben werden, falls nicht vorhanden.
        """
        try:
            text_instance = Editierbarer_Text.objects.get(identifier=identifier)
            return getattr(text_instance, attribute)
        except Editierbarer_Text.DoesNotExist:
            defaults = {
                "content": "Kein Text gefunden",
                "font": "JUNO Solar Lt",
                "font_size": 11,
                "x": 0,
                "y": 0,
            }
            return defaults.get(attribute, None)

    def fetch_x(self, identifier):
        x = self.get_attribute_by_identifier(identifier, "x")
        if x == 0:
            return self.l_margin
        return x

    def fetch_y(self, identifier):
        y = self.get_attribute_by_identifier(identifier, "y")
        if y == 0:
            y = self.get_y()
            return y
        return y


    def setup_text(self, identifier, content, h=5, bold=False, alignment="L"):
        """
        Richtet Text basierend auf einem Identifikator mit gegebenen Attributen im PDF aus.
        """
        font = self.get_attribute_by_identifier(identifier, "font")
        font_size = self.get_attribute_by_identifier(identifier, "font_size")
        self.set_font(font, "B" if bold else "", font_size)
        self.set_xy(self.fetch_x(identifier), self.fetch_y(identifier))
        self.multi_cell(0, h, content, 0, alignment)

    def setup_eintrag_text(
        self,
        identifier,
        eintrag_nummer,
        content_1,
        content_2="nach Auslegung",
        content_2_sub_1=None,
        content_2_sub_2=None,
        content_3="inklusive",
        content_4=None,
        additional_content=None,
        additional_content_2=None,
        h=5,
        bold=False,
        alignment="L",
    ):
        """
        Richtet mehrere Texteinheiten in einer Reihe basierend auf einem Identifikator aus.
        """
        font = self.get_attribute_by_identifier(identifier, "font")
        font_size = 11
        self.set_font(font, "B" if bold else "", font_size)

        x_initial = self.l_margin
        y = self.fetch_y(identifier) + 4

        content_settings = [
            (eintrag_nummer, x_initial, "L"),
            (content_1, 25, "L"),
            (content_2, 150, "L"),
            (content_3, 170, "R"),
        ]

        for content, x, align in content_settings:
            self.set_xy(x, y)
            self.cell(0, 6, content, 0, 0, align)

        tmp_y = y
        sub_contents = [(content_2_sub_1, None), (content_2_sub_2, None)]
        for content, _ in sub_contents:
            if content:
                y += 5
                x = 150
                self.set_xy(x, y)
                self.cell(0, 6, content, 0, 0, "L")

        y = tmp_y
        additional_contents = [(additional_content, None), (additional_content_2, None)]
        for content, _ in additional_contents:
            if content:
                y += 5
                x = (
                    self.fetch_x(identifier)
                    if self.get_attribute_by_identifier(identifier, "x") != 0
                    else 25
                )
                self.set_xy(x, y)
                self.cell(0, 6, content, 0, 0, "L")

        if content_4:
            font_size = self.get_attribute_by_identifier(identifier, "font_size")
            self.set_font(font, "B" if bold else "", font_size)
            y += 6
            x = (
                self.fetch_x(identifier)
                if self.get_attribute_by_identifier(identifier, "x") != 0
                else 25
            )
            self.set_xy(x, y)
            self.multi_cell(0, h, content_4, 0, alignment)

        if not content_4:
            y += 6
            self.set_y(y)

    def header(self):
        """
        Stellt das Kopfzeilen-Layout für jede Seite des PDFs bereit.
        """
        if "JUNO Solar Lt" not in self.fonts:
            regular_font_path = os.path.join(
                settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf"
            )
            bold_font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
            self.add_font("JUNO Solar Lt", "", regular_font_path, uni=True)
            self.add_font("JUNO Solar Lt", "B", bold_font_path, uni=True)

        self.set_y(0)
        self.set_font("JUNO Solar Lt", "", 8)
        self.set_text_color(0)
        header_text = f"Seite {self.page_no()}/{pages}       {self.title1}"
        self.cell(0, 10, header_text, 0, 0, "")

        if not self.is_last_page:
            self.set_y(15)
            self.set_font("JUNO Solar Lt", "", 12)
            self.set_x(40)
            if self.page_no() != 1:
                self.cell(0, 10, title, 0, 0, "")

            logo_path = os.path.join(settings.MEDIA_ROOT, "fonts/junosolar_logo.jpg")
            self.image(logo_path, x=167, y=10, w=30, h=15)
            self.ln(15)

    def footer(self):
        if not self.is_last_page:
            # Arial italic 8
            self.set_font("JUNO Solar Lt", "", 8)
            # Text color in gray
            self.set_text_color(128)
            # Position at 1.5 cm from bottom
            self.set_y(-25)
            self.set_x(25)
            self.multi_cell(0, 3, "Amtsgericht Chemnitz\nHR-Nr.:HRB 34192\nUSt.-ID: DE345149530\nSteuer-Nr.:227/156/19508\nGeschäftsführung: Denny Schädlich", 0, 0, "")  # type: ignore
            self.set_y(-25)
            self.set_x(85)
            centered_text1 = "Commerzbank Chemnitz\nIBAN: DE94 8704 0000 0770 0909 00\nBIC: COBADEFFXXX"
            self.multi_cell(0, 3, centered_text1, 0, "")
            self.set_y(-25)
            self.set_x(150)
            centered_text1 = "Volksbank Chemnitz\nIBAN: DE51 8709 6214 0321 1008 13\nBIC: GENODEF1CH1"
            self.multi_cell(0, 3, centered_text1, 0, "")

    def page1(self, data):
        self.add_page()

        # adresszeile_1
        adresszeile_1_content = self.get_attribute_by_identifier(
            "adresszeile_1", "content"
        )
        self.set_text_color(128)
        self.setup_text("adresszeile_1", adresszeile_1_content)

        # #############################
        self.ln(15)
        self.set_text_color(0)
        # #############################

        # kundendatei_variable
        kundendatei_variable_content = (
            f'{data["firma"]}\n{data["anrede"]} {data["kunde"]}\n{data["adresse"]}'
        )
        self.setup_text("kundendatei_variable", kundendatei_variable_content)

        # adresszeile_2
        adresszeile_2_content = self.get_attribute_by_identifier(
            "adresszeile_2", "content"
        )
        self.setup_text(
            "adresszeile_2", adresszeile_2_content, bold=True, alignment="R"
        )

        # adresszeile_3
        adresszeile_3_content = self.get_attribute_by_identifier(
            "adresszeile_3", "content"
        )
        self.setup_text("adresszeile_3", adresszeile_3_content, alignment="R")

        # vertriebdatei_variable
        vertriebdatei_variable_content = f'{data["vertriebler"]}\nDatum: {date.today().strftime("%d.%m.%Y")}\nwww.juno-solar.com'
        self.setup_text(
            "vertriebdatei_variable", vertriebdatei_variable_content, alignment="R"
        )
        # Überschrift und Text
        y = 100
        self.set_font("JUNO Solar Lt", "B", 17)
        self.set_x(0)
        self.set_y(y)
        self.cell(0, 6, "Zusätzliche Vereinbarung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_x(0)
        self.set_y(y + 10)
        self.cell(0, 5, f'Werdau, {date.today().strftime("%d.%m.%Y")}', 0, 0, "L")
        self.set_x(0)
        self.set_y(y + 20)
        self.multi_cell(
            0,
            5,
            "Im Folgenden werden die zusätzlich vereinbarten Änderungen an ihrer PV-Anlage festgehalten.",
            0,
            "",
        )
        # Tabelle Beginn
        # self.set_font("JUNO Solar Lt", "B", 12)
        # self.set_x(0)
        # self.set_y(135)
        # self.cell(0, 6, "Pos.", 0, 0, "L")
        # self.set_x(25)
        # self.cell(0, 6, "Bezeichnung", 0, 0, "L")
        # self.set_x(150)
        # self.cell(0, 6, "Menge", 0, 0, "L")
        # self.set_x(170)
        # self.cell(0, 6, "Gesamtpreis", 0, 0, "R")
        # self.line(10, 141, 200, 141)

        # tabelle_beginn_1
        tabelle_beginn_1 = self.get_attribute_by_identifier(
            "tabelle_beginn_1", "content"
        )
        self.setup_text(
            "tabelle_beginn_1", tabelle_beginn_1, h=6, bold=True, alignment="L"
        )

        # tabelle_beginn_2
        tabelle_beginn_2 = self.get_attribute_by_identifier(
            "tabelle_beginn_2", "content"
        )
        self.setup_text(
            "tabelle_beginn_2", tabelle_beginn_2, h=6, bold=True, alignment="L"
        )

        # tabelle_beginn_3
        tabelle_beginn_3 = self.get_attribute_by_identifier(
            "tabelle_beginn_3", "content"
        )
        self.setup_text(
            "tabelle_beginn_3", tabelle_beginn_3, h=6, bold=True, alignment="L"
        )

        # tabelle_beginn_4
        tabelle_beginn_4 = self.get_attribute_by_identifier(
            "tabelle_beginn_4", "content"
        )
        self.setup_text(
            "tabelle_beginn_4", tabelle_beginn_4, h=6, bold=True, alignment="R"
        )

        # #############################
        # line_1_page_1
        self.line(self.l_margin, self.get_y() + 0.5, 196.5, self.get_y() + 0.5)
        # #############################
        # Bestandteile Photovoltaikanlage
        tabelle_beginn_5 = self.get_attribute_by_identifier(
            "tabelle_beginn_5", "content"
        )
        self.setup_text(
            "tabelle_beginn_5", tabelle_beginn_5, h=6, bold=True, alignment="L"
        )
        tabelle_beginn_6 = self.get_attribute_by_identifier(
            "tabelle_beginn_6", "content"
        )
        self.setup_text("tabelle_beginn_6", tabelle_beginn_6, h=2, alignment="L")
        eintrag = 0
        y = 145
        # Tabelle Eintrag 1 NEU
        eintrag += 1
        tab1_eintrag_nummer = str(eintrag) + "."
        tab1_module = data["modulTicketArt"]
        tab1_module_props = f'∙ Leistung pro Modul: {str(data["wpModuleTicket"])} Wp\n∙ Produktgarantie: {str(data["produktGarantieTicket"])}\n∙ Leistungsgarantie: {str(data["leistungsGarantieTicket"])}'
        tab1_module_anzahl = f'{str(data["modulTicket"])} Stk'
        self.setup_eintrag_text(
            "tabelle_eintrag_1",
            tab1_eintrag_nummer,
            content_1=tab1_module,
            content_2=tab1_module_anzahl,
            content_3=convertCurrency("{:,.2f} €".format(data["modulTicketpreis"])),
            content_4=tab1_module_props,
        )

        y += 36
        # Tabelle Eintrag Optimierer
        if data["hersteller"] == "Huawei":
            if data["optimizerTicket"] > 0:
                # OPTIMIERER HUAWEI
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Huawei SUN2000-450W-P2 Moduloptimierer", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ Individuelle Schattenerkennung pro Modul\n∙ Produktgarantie: 25 Jahre\n",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["optimizerTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["optimizerTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                y += 16
            # Tabelle Eintrag 2X
            if data["batterieTicket"] > 0:
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 5, "Batteriespeicher: Huawei LUNA 2000", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.multi_cell(
                    0, 5, "Leistungsmodule\nBatteriemodule (je 5 kWh)", 0, 0, "L"
                )
                self.set_y(y + 15)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ max. Lade-/Entladeleistung: 5 kW\n∙ Produktgarantie: 10 Jahre",
                    0,
                    "L",
                )
                self.set_y(y + 5)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                leistungsmodule = ceil(
                    (int(data["batterieTicket"]) + int(data["batterieAnz"])) / 3
                ) - ceil(int(data["batterieAnz"]) / 3)
                self.multi_cell(0, 5, f"{str(leistungsmodule)} Stk" + "\n" + f'{str(data["batterieTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y + 5)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["leistungTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                self.set_y(y + 10)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["batterieTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                y += 27

            # Wand halterung
            if data["wandhalterungTicket"] > 0:
                # self.line(10, y + 3, 200, y + 3)
                # self.line(25, y + 7.5, 83, y + 7.5)
                # Tabelle Eintrag Optimierer
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Wandhalterung für Batteriespeicher", 0, 0, "L")
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["wandhalterungTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency(
                        "{:,.2f} €".format(data["wandhalterungTicketPreis"])
                    ),
                    0,
                    0,
                    "R",
                )
                y += 6
            if data["elwaTicket"] > 0:
                # Tabelle Eintrag Elwa
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "mypv AC ELWA 2", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ 0 - 3,5 KW stufenlos geregeltes Warmwasserbereitungsgerät\nfür netzgekoppelte Photovoltaikanlagen\n∙ Produktgarantie: 2 Jahre",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["elwaTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["elwaTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                y += 20
            if data["thorTicket"] > 0:
                # Tabelle Eintrag Thor
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "mypv AC∙THOR", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ 0- 3 KW stufenlos geregelter Photovoltaik Power-Manager\nfür Warmwasser, elektrische Wärmequellen und optional Heizung\n∙ Produktgarantie: 2 Jahre",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["thorTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency(
                        "{:,.2f} €".format(
                            data["thorTicketpreis"] + data["heizstabTicketpreis"]
                        )
                    ),
                    0,
                    0,
                    "R",
                )
                y += 5
                y += 15
            # Tabelle Eintrag Ersatzstrom
            if data["notstromTicket"] > 0:
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)

                self.cell(0, 6, "Viessmann VX3 Backup-Box", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)

                self.multi_cell(
                    0,
                    5,
                    "Dreiphasige Notstromversorgung bei Netzausfall\n∙ max. 40A pro Phase (bei Umgebungstemperatur von 35°C)\n∙ Produktgarantie: 2 Jahre",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["notstromTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["notstromTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                y += 15
        if data["hersteller"] == "Viessmann":
            if data["optimizerTicket"] > 0:
                # OPTIMIERER VIESSMANN
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Tigo TS4-A-0 Moduloptimierer", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ individuelle Schattenerkennung pro Modul\n∙ Produktgarantie: 25 Jahre",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["optimizerTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["optimizerTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                y += 17
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Tigo Acess Point (TAP)", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0, 6, "Drahtlose Kommunikation mit Tigo Smart Modulen", 0, 0, "L"
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, "1 Stk.", 0, "L")
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")

                y += 12

                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Tigo Cloud Connect Advances (CCA)", 0, 0, "L")
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, "1 Stk.", 0, "L")
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 7
            # Tabelle Eintrag 2X
            if data["batterieTicket"] > 0:
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 5, "Batteriespeicher: Huawei LUNA 2000", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.multi_cell(
                    0, 5, "Leistungsmodule\nBatteriemodule (je 5 kWh)", 0, 0, "L"
                )
                self.set_y(y + 15)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ max. Lade-/Entladeleistung: 5 kW\n∙ Produktgarantie: 10 Jahre",
                    0,
                    "L",
                )
                self.set_y(y + 5)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                leistungsmodule = ceil(
                    (int(data["batterieTicket"]) + int(data["batterieAnz"])) / 3
                ) - ceil(int(data["batterieAnz"]) / 3)
                self.multi_cell(0, 5, f"{str(leistungsmodule)} Stk" + "\n" + f'{str(data["batterieTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y + 5)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["leistungTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                self.set_y(y + 10)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["batterieTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                y += 26

            if data["thorTicket"] > 0:
                # Tabelle Eintrag Thor
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "mypv AC THOR", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ 0 - 3 KW stufenlos geregelter Photovoltaik Power-Manager\nfür Warmwasser, elektrische Wärmequellen und optional Heizun\n∙ Produktgarantie: 2 Jahre",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["thorTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency(
                        "{:,.2f} €".format(
                            data["thorTicketpreis"] + data["heizstabTicketpreis"]
                        )
                    ),
                    0,
                    0,
                    "R",
                )

                y += 19
            # Tabelle Eintrag Ersatzstrom
            if data["notstromTicket"] > 0:
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)

                self.cell(0, 6, "Viessmann VX3 Backup-Box", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)

                self.multi_cell(
                    0,
                    5,
                    "Dreiphasige Notstromversorgung bei Netzausfall\n∙ max. 40A pro Phase (bei Umgebungstemperatur von 35°C)\n∙ Produktgarantie: 2 Jahre",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, f'{str(data["notstromTicket"])} Stk', 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(
                    0,
                    6,
                    convertCurrency("{:,.2f} €".format(data["notstromTicketpreis"])),
                    0,
                    0,
                    "R",
                )
                y += 15

    def lastPage(self, data):
        self.add_page()
        # Aufpreissumme
        self.set_fill_color(240)
        self.set_y(35)
        self.set_font("JUNO Solar Lt", "B", 17)
        self.multi_cell(0, 6, "Aufpreissumme\n ", 0, "L", fill=True)
        self.set_font("JUNO Solar Lt", "", 12)
        self.set_y(45)
        steuer = data["steuersatz"]
        self.multi_cell(
            0,
            6,
            "Anlagengröße\n \nNetto\nMwSt. "
            + str(int(round(steuer * 100, 0)))
            + "%\nBrutto",
            0,
            "L",
            fill=True,
        )
        self.set_y(45)
        sum = float(data["ticketPreis"])
        netto = convertCurrency("{:,.2f} €".format(sum))
        mwst = convertCurrency("{:,.2f} €".format(sum * steuer))
        brutto = convertCurrency("{:,.2f} €".format(sum * (1 + steuer)))
        self.multi_cell(
            0,
            6,
            f'{str(data["kWp"])} kWp + {str(data["gewinnTicket"])} kwp = {str(round(data["kWp"] + data["gewinnTicket"],2))} kWp \n \n{netto}\n{mwst}',
            0,
            "R",
        )
        self.set_y(70)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, brutto, 0, 0, "R")
        self.line(175, 70, 197, 70)
        # Verbindlichkeiten
        verbindlichkeiten_1 = self.get_attribute_by_identifier(
            "verbindlichkeiten_1", "content"
        )
        self.setup_text(
            "verbindlichkeiten_1", verbindlichkeiten_1, bold=True, alignment="L"
        )
        verbindlichkeiten_2 = self.get_attribute_by_identifier(
            "verbindlichkeiten_2", "content"
        )
        self.setup_text("verbindlichkeiten_2", verbindlichkeiten_2, alignment="L")
        y = self.get_y()
        self.set_xy(105, y - 5)
        self.cell(0, 6, data["gueltig"], 0, 0, "L")
        self.set_y(y + 5)

        # Vollmacht
        vollmacht_1 = self.get_attribute_by_identifier("vollmacht_1", "content")
        self.setup_text("vollmacht_1", vollmacht_1, bold=True, alignment="L")
        vollmacht_2 = self.get_attribute_by_identifier("vollmacht_2", "content")
        self.setup_text("vollmacht_2", vollmacht_2, alignment="L")
        y = self.get_y()
        self.set_y(y + 5)
        # Garantiebediungen
        garantiebedingungen_1 = self.get_attribute_by_identifier(
            "garantiebedingungen_1", "content"
        )
        self.setup_text(
            "garantiebedingungen_1", garantiebedingungen_1, bold=True, alignment="L"
        )
        garantiebedingungen_2 = self.get_attribute_by_identifier(
            "garantiebedingungen_2", "content"
        )
        self.setup_text("garantiebedingungen_2", garantiebedingungen_2, alignment="L")
        y = self.get_y()
        self.set_y(y + 5)
        # Auftragserteilung
        auftragserteilung_1 = self.get_attribute_by_identifier(
            "auftragserteilung_1", "content"
        )
        self.setup_text(
            "auftragserteilung_1", auftragserteilung_1, bold=True, alignment="L"
        )
        auftragserteilung_2 = self.get_attribute_by_identifier(
            "auftragserteilung_2", "content"
        )
        self.setup_text("auftragserteilung_2", auftragserteilung_2, alignment="L")
        # Unterschriten
        self.set_font("JUNO Solar Lt", "", 12)
        self.set_y(255)
        self.cell(0, 6, "Datum", 0, 0, "L")
        self.line(self.l_margin, 255, 88, 255)
        self.set_x(46)
        self.cell(0, 6, "Unterschrift Auftraggeber", 0, 0, "L")
        self.set_x(120)
        self.cell(0, 6, "Datum", 0, 0, "L")
        self.line(120, 255, 198, 255)
        self.cell(0, 6, "Unterschrift Auftragnehmer", 0, 0, "R")
        self.set_y(250)
        self.set_x(120)
        self.cell(0, 6, datetime.now().strftime("%d.%m.%Y"), 0, 0, "L")
        self.image(
            os.path.join(settings.MEDIA_ROOT, "fonts/Stempel_Home.jpg"),
            x=160,
            y=230,
            w=32,
            h=24,
        )

    def page5(self):
        self.is_last_page = True
        self.add_page()
        self.set_text_color(0)
        self.set_auto_page_break(auto=True, margin=15)

        bold_texts = [
            # allgemeine_geschäftsbedingungen_bold_text_1
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_1", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_2
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_2", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_3
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_3", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_4
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_4", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_5
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_5", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_6
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_6", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_7
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_7", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_8
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_8", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_9
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_9", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_10
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_10", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_11
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_11", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_12
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_12", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_13
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_13", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_14
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_14", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_15
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_15", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_16
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_16", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_17
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_17", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_18
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_18", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_19
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_19", "content"
            ),
            # allgemeine_geschäftsbedingungen_bold_text_20
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_bold_text_20", "content"
            ),
        ]

        regular_texts = [
            # allgemeine_geschäftsbedingungen_regular_text_1
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_1", "content"
            ),
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_2", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_2
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_3", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_3
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_4", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_4
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_5", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_5
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_6", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_6
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_7", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_7
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_8", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_8
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_9", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_9
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_10", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_10
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_11", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_11
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_12", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_12
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_13", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_13
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_14", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_14
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_15", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_15
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_16", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_16
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_17", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_17
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_18", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_18
            self.get_attribute_by_identifier(
                "allgemeine_geschäftsbedingungen_regular_text_19", "content"
            ),  # allgemeine_geschäftsbedingungen_regular_text_19
        ]

        column_width = 1000
        columns_start_x = [
            15,
            self.w / 2 + 5,
        ]  # assuming two columns with the page split in the middle
        column = 0
        self.set_y(10)

        line_counter = 0

        for bold, regular in zip(bold_texts, regular_texts):
            # Check if adding more strings would exceed the 200-string limit
            bold_lines = len(bold.split("\n"))
            regular_lines = len(regular.split("\n"))

            if line_counter + bold_lines + regular_lines > 96:
                if column == 1:  # If it's the second column, we add a new page.
                    self.add_page()
                    column = 0  # Reset to first column
                else:
                    column += 1  # Move to the next column
                self.set_y(10)  # Reset y to top
                line_counter = 0  # Reset line counter for new column/columns

            # Set x position based on column
            self.set_x(columns_start_x[column])

            # Print bold text
            self.set_font("JUNO Solar Lt", "B", 8)
            self.set_font_size_to_fit(bold, column_width)
            self.multi_cell(column_width, 3.2, txt=bold)
            line_counter += bold_lines

            self.set_x(columns_start_x[column])
            # Print regular text
            self.set_font("JUNO Solar Lt", "", 8)
            self.set_font_size_to_fit(regular, column_width)
            self.multi_cell(column_width, 3.2, txt=regular)
            line_counter += regular_lines

    def set_font_size_to_fit(self, text, width=1000):
        # Current size and width of the text
        current_size = self.font_size_pt
        current_width = 1000

        # Check if the text is already smaller than the width
        if current_width <= width:
            return

        # Calculate required font size
        font_size = current_size * width / current_width

        # Set the font size
        self.set_font_size(font_size)


def createTicketPdf(data):
    global title, pages
    title1 = ""
    pages = 4

    pdf = PDF(title1)
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")

    # create the ticket-PDF
    pdf.page1(data)
    pdf.lastPage(data)
    pdf.page5()

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content
