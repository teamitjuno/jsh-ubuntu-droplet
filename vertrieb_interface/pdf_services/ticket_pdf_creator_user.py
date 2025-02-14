from datetime import datetime, date
from math import ceil
from fpdf import FPDF
from config import settings
from vertrieb_interface.pdf_services.helper_functions import convertCurrency
from vertrieb_interface.models import Editierbarer_Text
from vertrieb_interface.pdf_services.angebot_pdf_creator_user import agbPage, certPage, page4, anzahlZubehoer, replace_spaces_with_underscores
import os

title = ""
pages = 6

class PDF(FPDF):
    """
    Diese Klasse erzeugt ein PDF-Dokument mit spezifischem Layout und Inhalt.
    """

    def __init__(self, title1, *args, **kwargs):
        """
        Initialisiert das PDF-Objekt mit spezifischen Margen und Linienbreiten.
        """
        super(PDF, self).__init__(*args, **kwargs)
        self.is_last_page = False
        self.skip_logo = False
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

    def get_anrede_content(self, data):
        """
        Generiert eine Anrede basierend auf dem Anredefeld in den Daten.
        """
        if "Firma" in data["anrede"] or "Familie" in data["anrede"]:
            anrede_content = "Sehr geehrte Damen und Herren"
        elif "Herr" in data["anrede"]:
            anrede_content = f'Sehr geehrter {data["anrede"]} {data["kunde"]},'
        else:
            anrede_content = f'Sehr geehrte {data["anrede"]} {data["kunde"]},'

        return anrede_content

    def get_entladeleistung(self, data, batterieModell):
        """
        Ruft die Lade/Entladeleistung basierend auf der Anzahl der Batterien ab.
        """
        if batterieModell == "LUNA 2000-7-S1":
            entladeleistung = self.get_attribute_by_identifier(
                "tabelle_eintrag_4_huawei7_3", "content"
            )
        else:
            if str(data["batterieAnz"]) == "1":
                entladeleistung = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_huawei5_3", "content"
                )
            elif data["batterieAnz"] >= 2 and data["batterieAnz"] <= 3:
                entladeleistung = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_huawei5_4", "content"
                )
            else:
                entladeleistung = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_huawei5_5", "content"
                )
        return entladeleistung

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
        if "Poppins" not in self.fonts:
            regular_font_path = os.path.join(
                settings.STATIC_ROOT, "fonts/Poppins-Regular.ttf"
            )
            bold_font_path = os.path.join(settings.STATIC_ROOT, "fonts/Poppins-Bold.ttf")
            self.add_font("Poppins", "", regular_font_path, uni=True)
            self.add_font("Poppins", "B", bold_font_path, uni=True)

        self.set_y(0)
        self.set_font("JUNO Solar Lt", "", 8)
        self.set_text_color(0)
        header_text = f"Seite {self.page_no()}/{pages}       {self.title1}"
        self.cell(0, 10, header_text, 0, 0, "")

        if not self.skip_logo:
            self.set_y(15)
            self.set_font("JUNO Solar Lt", "", 12)
            self.set_x(40)
            if self.page_no() != 1:
                self.cell(0, 10, title, 0, 0, "")

            logo_path = os.path.join(settings.STATIC_ROOT, "fonts/junosolar_logo.jpg")
            self.image(logo_path, x=167, y=10, w=30, h=15)
            self.ln(15)

    def footer(self):
        """
        Richtet die Fußzeile für das PDF ein, die auf jeder Seite wiederholt wird.
        """
        if not self.is_last_page:
            self.set_text_color(128)
            for footer_index in range(1, 4):
                footer_prefix = f"footer_{footer_index}"
                content = self.get_attribute_by_identifier(footer_prefix, "content")
                self.setup_text(footer_prefix, content, h=3, bold=False, alignment="L")

    def page1(self, data, eintrag):
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

        # ANGEBOT_untertitel
        if data["istNachkauf"]:
            ANGEBOT_untertitel_content = self.get_attribute_by_identifier(
                "ANGEBOT_untertitel", "content"
            )
            self.setup_text(
                "ANGEBOT_untertitel",
                ANGEBOT_untertitel_content,
                h=6,
                bold=True,
                alignment="L",
            )
        else:
            ANGEBOT_untertitel_content = self.get_attribute_by_identifier(
                "ZUSATZ_untertitel", "content"
            )
            self.setup_text(
                "ZUSATZ_untertitel",
                ANGEBOT_untertitel_content,
                h=6,
                bold=True,
                alignment="L",
            )

        # ANGEBOT_id_nummer (variable)
        ANGEBOT_id_nummer = f"{self.title1}"
        self.setup_text(
            "ANGEBOT_id_nummer", ANGEBOT_id_nummer, h=6, bold=True, alignment="R"
        )

        # uberschrift_und_text_1
        uberschrift_und_text_1_content = self.get_attribute_by_identifier(
            "uberschrift_und_text_1", "content"
        )
        self.setup_text(
            "uberschrift_und_text_1", uberschrift_und_text_1_content, alignment="L"
        )

        # kWp_und_standort (variable)
        kWp_und_standort_content = f'{str(data["existing_kWp"])} kWp + {str(data["ticket_kWp"])} kWp = {str(data["kWp"])} kWp\n{data["standort"]}'
        self.setup_text("kWp_und_standort", kWp_und_standort_content, alignment="L")

        # anrede_content
        anrede_content = self.get_anrede_content(data)
        self.setup_text("anrede_content", anrede_content, h=6)

        # uberschrift_und_text_2
        uberschrift_und_text_2_content = self.get_attribute_by_identifier(
            "uberschrift_und_text_2_ticket", "content"
        )
        self.setup_text(
            "uberschrift_und_text_2_ticket", uberschrift_und_text_2_content, alignment="LR"
        )

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

        # Tabelle Eintrag 1
        # Solar Module
        eintrag += 1
        tab1_eintrag_nummer = str(eintrag) + "."
        tab1_module = data["module"]
        tab1_module_props = f'∙ Leistung pro Modul: {str(data["wpModule"])} Wp\n∙ Produktgarantie: {str(data["produktGarantie"])}\n∙ Leistungsgarantie: {str(data["leistungsGarantie"])}'
        tab1_module_anzahl = f'{str(data["anzModule"])}'
        self.setup_eintrag_text(
            "tabelle_eintrag_1",
            tab1_eintrag_nummer,
            content_1=tab1_module,
            content_2=tab1_module_anzahl,
            content_4=tab1_module_props,
        )

        # Tabelle Eintrag 3
        if data["smartmeterModell"] != "kein EMS":
            eintrag += 1
            tab3_eintrag_nummer = str(eintrag) + "."
            tab3_energiezahler = "Huawei " + data["smartmeterModell"]
            tab3_energiezahler_props = self.get_attribute_by_identifier(
                "tabelle_eintrag_3_huawei_2", "content"
            )
            self.setup_eintrag_text(
                "tabelle_eintrag_3_huawei_2",
                tab3_eintrag_nummer,
                tab3_energiezahler,
                content_4=tab3_energiezahler_props,
            )

        # Tabelle Eintrag 4
        # Batteriespeicher
        if data["batterieVorh"]:
            batterieDict = {"LUNA 2000-5-S0": 5, "LUNA 2000-7-S1": 7}
            batterieTyp = batterieDict.get(str(data["batterieModell"]))
            eintrag += 1
            tab4_eintrag_nummer = str(eintrag) + "."
            tab4_content2_sub1 = str(data["leistModAnz"])
            tab4_content2_sub2 = str(data["batterieAnz"])
            tab4_batterie_speicher = self.get_attribute_by_identifier(
                f"tabelle_eintrag_4_huawei{batterieTyp}_1", "content"
            )
            tab4_additional_content2 = self.get_attribute_by_identifier(
                f"tabelle_eintrag_4_huawei{batterieTyp}_2", "content"
            )
            tab4_additional_content = "Leistungsmodule"
            tab4_batterie_speicher_props = self.get_entladeleistung(data, str(data["batterieModell"]))
            self.setup_eintrag_text(
                f"tabelle_eintrag_4_huawei{batterieTyp}_3",
                tab4_eintrag_nummer,
                tab4_batterie_speicher,
                content_2="",
                content_4=tab4_batterie_speicher_props,
                content_2_sub_1=tab4_content2_sub1,
                content_2_sub_2=tab4_content2_sub2,
                additional_content=tab4_additional_content,
                additional_content_2=tab4_additional_content2,
                alignment="",
            )
            # Bei Austausch des Speichertyps den Speicher aus angenommenem Angebot wieder abziehen
            if data["batterieModellOrig"] and data["batterieModellOrig"] != data["batterieModell"]:
                eintrag += 1
                batterieTypOrig = batterieDict.get(str(data["batterieModellOrig"]))
                tab4o_eintrag_nummer = str(eintrag) + "."
                tab4o_content2_sub1 = str(-data["leistModAnzOrig"])
                tab4o_content2_sub2 = str(-data["batterieAnzOrig"])
                tab4o_batterie_speicher = self.get_attribute_by_identifier(
                    f"tabelle_eintrag_4_huawei{batterieTypOrig}_1", "content"
                )
                tab4o_additional_content2 = self.get_attribute_by_identifier(
                    f"tabelle_eintrag_4_huawei{batterieTypOrig}_2", "content"
                )
                tab4o_additional_content = "Leistungsmodule"
                tab4o_batterie_speicher_props = self.get_entladeleistung(data, str(data["batterieModellOrig"]))
                self.setup_eintrag_text(
                    f"tabelle_eintrag_4_huawei{batterieTypOrig}_3",
                    tab4o_eintrag_nummer,
                    tab4o_batterie_speicher,
                    content_2="",
                    content_4=tab4o_batterie_speicher_props,
                    content_2_sub_1=tab4o_content2_sub1,
                    content_2_sub_2=tab4o_content2_sub2,
                    additional_content=tab4o_additional_content,
                    additional_content_2=tab4o_additional_content2,
                    alignment="",
                )
        return eintrag

    def pricePage(self, data):
        self.add_page()
        self.is_last_page = False
        # Angebotssumme
        self.set_fill_color(240)
        self.set_y(35)
        self.set_font("JUNO Solar Lt", "B", 17)
        if data["istNachkauf"]:
            self.multi_cell(0, 6, "Angebotssumme\n ", 0, "L", fill=True)
            self.set_font("JUNO Solar Lt", "", 12)
            self.set_y(45)
            steuer = data["steuersatz"]
            self.cell(0, 6, "Anlagengröße", 0, 1, "L", fill=True)
            self.cell(0, 6, "", 0, 1, "L", fill=True)
            self.cell(0, 6, "Investitionskosten", 0, 1, "L", fill=True)
            self.cell(0, 6, "zzgl. MwSt.", 0, 1, "L", fill=True)
            self.set_font("JUNO Solar Lt", "B", 12)
            self.cell(0, 6, "Ihre Investition (inkl. MwSt.)", 0, 1, "L", fill=True)
        else:
            self.multi_cell(0, 6, "Aufpreissumme\n ", 0, "L", fill=True)
            self.set_font("JUNO Solar Lt", "", 12)
            self.set_y(45)
            steuer = data["steuersatz"]
            self.cell(0, 6, "Anlagengröße", 0, 1, "L", fill=True)
            self.cell(0, 6, "", 0, 1, "L", fill=True)
            self.cell(0, 6, "zusätzliche Kosten", 0, 1, "L", fill=True)
            self.cell(0, 6, "zzgl. MwSt.", 0, 1, "L", fill=True)
            self.set_font("JUNO Solar Lt", "B", 12)
            self.cell(0, 6, "Ihre zusätzlichen Kosten (inkl. MwSt.)", 0, 1, "L", fill=True)
        self.set_font("JUNO Solar Lt", "", 12)
        self.set_y(45)
        sum = data["kostenPVA"]
        netto = convertCurrency("{:,.2f} €".format(sum))
        mwst = convertCurrency("{:,.2f} €".format(sum * steuer))
        brutto = convertCurrency("{:,.2f} €".format(sum * (1 + steuer)))
        self.cell(0, 6, f'{str(data["existing_kWp"])} kWp + {str(data["ticket_kWp"])} kWp = {str(data["kWp"])} kWp', 0, 1, "R")
        self.cell(0, 6, "", 0, 1, "R")
        self.cell(0, 6, netto, 0, 1, "R")
        self.cell(0, 6, mwst, 0, 1, "R")
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, brutto, 0, 1, "R")
        self.line(175, 69, 197, 69)
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


def createOfferPdf(data, vertrieb_ticket, certifikate, user):
    global title, pages
    title1 = f"{vertrieb_ticket.ticket_id}"
    pages = 4
    if certifikate:
        pages += 1
    zubehoerLimit = 13
    if data["wallboxAnz"] > 0:
        zubehoerLimit -= 1
    if data["batterieVorh"]:
        zubehoerLimit += 1
        if data["batterieModellOrig"] and data["batterieModellOrig"] != data["batterieModell"]:
            zubehoerLimit += 1
    if data["smartmeterModell"] == "kein EMS":
        zubehoerLimit -= 1
    anzZubehoer = anzahlZubehoer(data)
    if anzZubehoer > 0 or data["wallboxVorh"] or data["kWp"] >= 25.0:
        pages += 1
    # second page for additional Zubehör
    if (data["wallboxAnz"] > 0 and anzZubehoer > 9) or anzZubehoer > 11:
        pages += 1

    pdf = PDF(title1)
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")
    pdf.set_creator(f"{user.first_name} {user.last_name})")
    # create the offer-PDF
    eintrag = 0
    eintrag = pdf.page1(data, eintrag)
    pdf, eintrag = page4(pdf, data, eintrag, zubehoerLimit)

    pdf.pricePage(data)
    pdf = certPage(pdf, certifikate)
    pdf = agbPage(pdf)

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content
