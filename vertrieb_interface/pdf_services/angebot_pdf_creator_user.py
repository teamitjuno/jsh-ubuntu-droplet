from datetime import datetime, date
from math import ceil
from fpdf import FPDF
from config import settings
from vertrieb_interface.pdf_services.helper_functions import convertCurrency
from vertrieb_interface.models import Editierbarer_Text
from vertrieb_interface.pdf_services.calc_pdf_creator import calcPage1, calcPage2
import os

title = ""
pages = 6
global zubehoerLimitMitWallbox, zubehoerLimitOhneWallbox

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

    def get_entladeleistung(self, data):
        """
        Ruft die Lade/Entladeleistung basierend auf der Anzahl der Batterien ab.
        """
        if str(data["hersteller"]) == "Viessmann":
            if str(data["batterieAnz"]) == "1":
                entladeleistung = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_viessman_3", "content"
                )
            elif str(data["batterieAnz"]) == "2":
                entladeleistung = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_viessman_4", "content"
                )
            else:
                entladeleistung = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_viessman_5", "content"
                )
        elif str(data["hersteller"]) == "Huawei":
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
        kWp_und_standort_content = f'{str(data["kWp"])} kWp\n{data["standort"]}'
        self.setup_text("kWp_und_standort", kWp_und_standort_content, alignment="L")

        # anrede_content
        anrede_content = self.get_anrede_content(data)
        self.setup_text("anrede_content", anrede_content, h=6)

        # uberschrift_und_text_2
        uberschrift_und_text_2_content = self.get_attribute_by_identifier(
            "uberschrift_und_text_2", "content"
        )
        self.setup_text(
            "uberschrift_und_text_2", uberschrift_und_text_2_content, alignment="LR"
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
        tab1_module_anzahl = f'{str(data["anzModule"])} Stk'
        self.setup_eintrag_text(
            "tabelle_eintrag_1",
            tab1_eintrag_nummer,
            content_1=tab1_module,
            content_2=tab1_module_anzahl,
            content_4=tab1_module_props,
        )

        if data["hersteller"] == "Viessmann":

            # Tabelle Eintrag 2
            # Wechselrichter

            eintrag += 1
            tab2_eintrag_nummer = str(eintrag) + "."
            tab2_wr_model = self.get_attribute_by_identifier(
                "tabelle_eintrag_2_viessman_1", "content"
            )
            garantie = str(data["garantieJahre"])
            tab2_wr_model_props = f"{self.get_attribute_by_identifier('tabelle_eintrag_2_huawei_2', 'content')} {garantie}"
            self.setup_eintrag_text(
                "tabelle_eintrag_2_viessman_2",
                tab2_eintrag_nummer,
                tab2_wr_model,
                content_4=tab2_wr_model_props,
            )

            # Tabelle Eintrag 3
            eintrag += 1
            tab3_eintrag_nummer = str(eintrag) + "."
            tab3_energiezahler = data["smartmeterModell"]
            garantie = str(data["garantieJahre"])
            tab3_energiezahler_props = f'{self.get_attribute_by_identifier("tabelle_eintrag_3_viessman_2", "content")}'

            self.setup_eintrag_text(
                "tabelle_eintrag_3_viessman_2",
                tab3_eintrag_nummer,
                tab3_energiezahler,
                content_4=tab3_energiezahler_props,
            )

            # Tabelle Eintrag 4
            # Batteriespeicher

            if data["batterieVorh"]:

                eintrag += 1
                tab4_eintrag_nummer = str(eintrag) + "."
                tab4_batterie_speicher = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_viessman_1", "content"
                )
                tab4_content2 = str(data["batterieAnz"])
                tab4_additional_content = self.get_attribute_by_identifier(
                    "tabelle_eintrag_4_viessman_2", "content"
                )
                tab4_entladeleistung = self.get_entladeleistung(data)

                self.setup_eintrag_text(
                    "tabelle_eintrag_4_viessman_3",
                    tab4_eintrag_nummer,
                    tab4_batterie_speicher,
                    content_2="",
                    content_4=tab4_entladeleistung,
                    additional_content=tab4_additional_content,
                    content_2_sub_1=tab4_content2,
                    alignment="",
                )

        elif data["hersteller"] == "Huawei":

            # Tabelle Eintrag 2
            # Wechselrichter
            eintrag += 1
            tab2_eintrag_nummer = str(eintrag) + "."
            tab2_wr_model = self.get_attribute_by_identifier(
                "tabelle_eintrag_2_huawei_1", "content"
            )
            garantie = str(data["garantieJahre"])
            tab2_wr_model_props = f"{self.get_attribute_by_identifier('tabelle_eintrag_2_huawei_2', 'content')} {garantie}"
            self.setup_eintrag_text(
                "tabelle_eintrag_2_huawei_2",
                tab2_eintrag_nummer,
                tab2_wr_model,
                content_4=tab2_wr_model_props,
            )

            # Tabelle Eintrag 3

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
                eintrag += 1
                tab4_eintrag_nummer = str(eintrag) + "."
                tab4_content2_sub1 = str(ceil(data["batterieAnz"] / 3))
                tab4_content2_sub2 = str(data["batterieAnz"])
                if data["batterieModell"] == "LUNA 2000-5-S0":
                    tab4_batterie_speicher = self.get_attribute_by_identifier(
                        "tabelle_eintrag_4_huawei5_1", "content"
                    )
                    tab4_additional_content2 = self.get_attribute_by_identifier(
                        "tabelle_eintrag_4_huawei5_2", "content"
                    )
                    tab4_additional_content = "Leistungsmodule"
                    tab4_batterie_speicher_props = self.get_entladeleistung(data)
                    self.setup_eintrag_text(
                        "tabelle_eintrag_4_huawei5_3",
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
                elif data["batterieModell"] == "LUNA 2000-7-S1":
                    tab4_batterie_speicher = self.get_attribute_by_identifier(
                        "tabelle_eintrag_4_huawei7_1", "content"
                    )
                    tab4_additional_content2 = self.get_attribute_by_identifier(
                        "tabelle_eintrag_4_huawei7_2", "content"
                    )
                    tab4_additional_content = "Leistungsmodule"
                    tab4_batterie_speicher_props = self.get_attribute_by_identifier(
                        "tabelle_eintrag_4_huawei7_3", "content"
                    )
                    self.setup_eintrag_text(
                        "tabelle_eintrag_4_huawei7_3",
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
        return eintrag

    def page2(self, data, eintrag):
        self.add_page()

        # Tabelle Eintrag 5
        # Unterkonstruktion
        eintrag += 1
        tab5_eintrag_nummer = str(eintrag) + "."
        tab5_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_5_1", "content"
        )
        tab5_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_5_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_5_2",
            tab5_eintrag_nummer,
            tab5_content_1,
            content_4=tab5_content_4,
        )

        # Tabelle Eintrag 6
        # Solarleitung
        eintrag += 1
        tab6_eintrag_nummer = str(eintrag) + "."
        tab6_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_6_1", "content"
        )
        tab6_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_6_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_6_2",
            tab6_eintrag_nummer,
            tab6_content_1,
            content_4=tab6_content_4,
        )

        # Tabelle Eintrag 7
        # Stecker und Buchsen
        eintrag += 1
        tab7_eintrag_nummer = str(eintrag) + "."
        tab7_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_7_1", "content"
        )
        tab7_content_4 = ""
        self.setup_eintrag_text(
            "tabelle_eintrag_7_1",
            tab7_eintrag_nummer,
            tab7_content_1,
            content_4=tab7_content_4,
        )

        # Tabelle Eintrag 8
        # Kabelkanäle
        eintrag += 1
        tab8_eintrag_nummer = str(eintrag) + "."
        tab8_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_8_1", "content"
        )
        tab8_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_8_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_8_2",
            tab8_eintrag_nummer,
            tab8_content_1,
            content_4=tab8_content_4,
        )

        ######################################################################
        # line_1_page_2
        self.line(self.l_margin, self.get_y() + 5, 196.5, self.get_y() + 5)
        ######################################################################

        # Gleichstromseitige Installation
        gleichstromseitige_installation_1 = self.get_attribute_by_identifier(
            "gleichstromseitige_installation_1", "content"
        )
        self.setup_text(
            "gleichstromseitige_installation_1",
            gleichstromseitige_installation_1,
            bold=True,
            alignment="L",
        )
        gleichstromseitige_installation_2 = self.get_attribute_by_identifier(
            "gleichstromseitige_installation_2", "content"
        )
        self.setup_text(
            "gleichstromseitige_installation_2",
            gleichstromseitige_installation_2,
            alignment="L",
        )

        # Tabelle Eintrag 9
        eintrag += 1
        tab9_eintrag_nummer = str(eintrag) + "."
        tab9_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_9_1", "content"
        )
        tab9_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_9_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_9_2",
            tab9_eintrag_nummer,
            tab9_content_1,
            content_2="1",
            content_4=tab9_content_4,
        )

        # Tabelle Eintrag 10
        eintrag += 1
        tab10_eintrag_nummer = str(eintrag) + "."
        tab10_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_10_1", "content"
        )
        tab10_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_10_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_10_2",
            tab10_eintrag_nummer,
            tab10_content_1,
            content_4=tab10_content_4,
        )

        # Tabelle Eintrag 11

        eintrag += 1
        tab11_eintrag_nummer = str(eintrag) + "."
        tab11_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_11_1", "content"
        )
        tab11_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_11_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_11_2",
            tab11_eintrag_nummer,
            tab11_content_1,
            content_4=tab11_content_4,
        )

        ######################################################
        # line_2_page_2
        self.line(self.l_margin, self.get_y() + 5, 196.5, self.get_y() + 5)
        ######################################################

        # Wechselstromseitige Installation und Inbetriebnahme
        wechselstromseitige_installation_und_inbetriebnahme_1 = (
            self.get_attribute_by_identifier(
                "wechselstromseitige_installation_und_inbetriebnahme_1", "content"
            )
        )
        self.setup_text(
            "wechselstromseitige_installation_und_inbetriebnahme_1",
            wechselstromseitige_installation_und_inbetriebnahme_1,
            bold=True,
            alignment="L",
        )
        wechselstromseitige_installation_und_inbetriebnahme_2 = (
            self.get_attribute_by_identifier(
                "wechselstromseitige_installation_und_inbetriebnahme_2", "content"
            )
        )
        self.setup_text(
            "wechselstromseitige_installation_und_inbetriebnahme_2",
            wechselstromseitige_installation_und_inbetriebnahme_2,
            alignment="L",
        )

        # Tabelle Eintrag 12
        # AC-Installation

        eintrag += 1
        tab12_eintrag_nummer = str(eintrag) + "."
        tab12_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_12_1", "content"
        )
        tab12_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_12_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_12_2",
            tab12_eintrag_nummer,
            tab12_content_1,
            content_2="1",
            content_4=tab12_content_4,
        )

        # Tabelle Eintrag 13
        # Netzanschluss

        eintrag += 1
        tab13_eintrag_nummer = str(eintrag) + "."
        tab13_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_13_1", "content"
        )
        tab13_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_13_2", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_13_2",
            tab13_eintrag_nummer,
            tab13_content_1,
            content_2="1",
            content_4=tab13_content_4,
        )

        # Tabelle Eintrag 14
        # Installation und Parametrierung des Wechselrichters

        eintrag += 1
        tab14_eintrag_nummer = str(eintrag) + "."
        tab14_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_14", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_14",
            tab14_eintrag_nummer,
            tab14_content_1,
            content_2="1",
        )

        ######################################################
        # line_3_page_2
        self.line(self.l_margin, self.get_y() + 5, 196.5, self.get_y() + 5)
        ######################################################
        return eintrag

    def page3(self, data, eintrag):
        self.add_page()
        # Anlagenüberwachung und Visualisierung
        anlagenüberwachung_und_visualisierung_1 = self.get_attribute_by_identifier(
            "anlagenüberwachung_und_visualisierung_1", "content"
        )
        self.setup_text(
            "anlagenüberwachung_und_visualisierung_1",
            anlagenüberwachung_und_visualisierung_1,
            bold=True,
            alignment="L",
        )
        anlagenüberwachung_und_visualisierung_2 = self.get_attribute_by_identifier(
            "anlagenüberwachung_und_visualisierung_2", "content"
        )
        self.setup_text(
            "anlagenüberwachung_und_visualisierung_2",
            anlagenüberwachung_und_visualisierung_2,
            alignment="L",
        )

        # Tabelle Eintrag 15

        if data["hersteller"] == "Viessmann":
            eintrag += 1
            tab15_eintrag_nummer = str(eintrag) + "."
            tab15_content_1 = self.get_attribute_by_identifier(
                "tabelle_eintrag_15", "content"
            )
            tab15_content_4 = self.get_attribute_by_identifier(
                "tabelle_eintrag_15_viessman", "content"
            )
            self.setup_eintrag_text(
                "tabelle_eintrag_15_viessman",
                tab15_eintrag_nummer,
                tab15_content_1,
                content_2="1",
                content_4=tab15_content_4,
            )

        if data["hersteller"] == "Huawei":
            eintrag += 1
            tab15_eintrag_nummer = str(eintrag) + "."
            tab15_content_1 = self.get_attribute_by_identifier(
                "tabelle_eintrag_15", "content"
            )
            tab15_content_4 = self.get_attribute_by_identifier(
                "tabelle_eintrag_15_huawei", "content"
            )
            self.setup_eintrag_text(
                "tabelle_eintrag_15_huawei",
                tab15_eintrag_nummer,
                tab15_content_1,
                content_2="1",
                content_4=tab15_content_4,
            )

        ###########################################################################
        self.line(self.l_margin, self.get_y() + 5, 196.5, self.get_y() + 5)
        ###########################################################################

        # Netzanschlussmanagement

        netzanschlussmanagement_1 = self.get_attribute_by_identifier(
            "netzanschlussmanagement_1", "content"
        )
        self.setup_text(
            "netzanschlussmanagement_1",
            netzanschlussmanagement_1,
            bold=True,
            alignment="L",
        )
        netzanschlussmanagement_2 = self.get_attribute_by_identifier(
            "netzanschlussmanagement_2", "content"
        )
        self.setup_text(
            "netzanschlussmanagement_2", netzanschlussmanagement_2, alignment="L"
        )

        # Tabelle Eintrag 16
        eintrag += 1
        tab16_eintrag_nummer = str(eintrag) + "."
        tab16_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_16", "content"
        )
        tab16_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_16_1", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_16_1",
            tab16_eintrag_nummer,
            tab16_content_1,
            content_2="1",
            content_4=tab16_content_4,
        )

        # Tabelle Eintrag 17
        eintrag += 1
        tab17_eintrag_nummer = str(eintrag) + "."
        tab17_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_17", "content"
        )
        tab17_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_17_1", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_17_1",
            tab17_eintrag_nummer,
            tab17_content_1,
            content_2="1",
            content_4=tab17_content_4,
        )

        # Tabelle Eintrag 18
        eintrag += 1
        tab18_eintrag_nummer = str(eintrag) + "."
        tab18_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_18", "content"
        )
        tab18_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_18_1", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_18_1",
            tab18_eintrag_nummer,
            tab18_content_1,
            content_2="1",
            content_4=tab18_content_4,
        )

        # Tabelle Eintrag 19
        eintrag += 1
        tab19_eintrag_nummer = str(eintrag) + "."
        tab19_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_19", "content"
        )
        tab19_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_19_1", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_19_1",
            tab19_eintrag_nummer,
            tab19_content_1,
            content_2="1",
            content_4=tab19_content_4,
        )

        # Tabelle Eintrag 20
        if data["kWp"] >= 25.0:
            eintrag += 1
            tab20_eintrag_nummer = str(eintrag) + "."
            tab20_content_1 = self.get_attribute_by_identifier(
                "tabelle_eintrag_20", "content"
            )
            tab20_content_4 = self.get_attribute_by_identifier(
                "tabelle_eintrag_20_1", "content"
            )
            self.setup_eintrag_text(
                "tabelle_eintrag_20_1",
                tab20_eintrag_nummer,
                tab20_content_1,
                content_2="1",
                content_4=tab20_content_4,
            )

        ###################################################################
        # line_2_page_3
        self.line(self.l_margin, self.get_y() + 5, 196.5, self.get_y() + 5)
        self.set_y(self.get_y() + 10)
        ###################################################################

        # Zusätzliche Leistungen
        zusätzliche_leistungen_1 = self.get_attribute_by_identifier(
            "zusätzliche_leistungen_1", "content"
        )
        self.setup_text(
            "zusätzliche_leistungen_1",
            zusätzliche_leistungen_1,
            bold=True,
            alignment="L",
        )
        zusätzliche_leistungen_2 = self.get_attribute_by_identifier(
            "zusätzliche_leistungen_2", "content"
        )
        self.setup_text(
            "zusätzliche_leistungen_2", zusätzliche_leistungen_2, alignment="L"
        )

        # Tabelle Eintrag 21
        eintrag += 1
        tab21_eintrag_nummer = str(eintrag) + "."
        tab21_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_21", "content"
        )
        tab21_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_21_1", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_21_1",
            tab21_eintrag_nummer,
            tab21_content_1,
            content_2="1",
            content_4=tab21_content_4,
        )

        # Tabelle Eintrag 22
        eintrag += 1
        tab22_eintrag_nummer = str(eintrag) + "."
        tab22_content_1 = self.get_attribute_by_identifier(
            "tabelle_eintrag_22", "content"
        )
        tab22_content_4 = self.get_attribute_by_identifier(
            "tabelle_eintrag_22_1", "content"
        )
        self.setup_eintrag_text(
            "tabelle_eintrag_22_1",
            tab22_eintrag_nummer,
            tab22_content_1,
            content_2="1",
            content_4=tab22_content_4,
        )

        # Tabelle Eintrag 23
        if data["kWp"] < 25.0:
            eintrag += 1
            tab23_eintrag_nummer = str(eintrag) + "."
            tab23_content_1 = self.get_attribute_by_identifier(
                "tabelle_eintrag_23", "content"
            )
            tab23_content_4 = self.get_attribute_by_identifier(
                "tabelle_eintrag_23_1", "content"
            )
            self.setup_eintrag_text(
                "tabelle_eintrag_23_1",
                tab23_eintrag_nummer,
                tab23_content_1,
                content_2="1",
                content_4=tab23_content_4,
            )

        return eintrag

    def page4(self, data, eintrag):
        zubehoerVorhanden = anzahlZubehoer(data) > 0
        if zubehoerVorhanden or data["wallboxVorh"] or data["kWp"] >= 25.0:
            self.add_page()

        if data["kWp"] >= 25.0:
            # Tabelle Eintrag 23
            eintrag += 1
            tab23_eintrag_nummer = str(eintrag) + "."
            tab23_content_1 = self.get_attribute_by_identifier(
                "tabelle_eintrag_23", "content"
            )
            tab23_content_4 = self.get_attribute_by_identifier(
                "tabelle_eintrag_23_1", "content"
            )
            self.setup_eintrag_text(
                "tabelle_eintrag_23_1",
                tab23_eintrag_nummer,
                tab23_content_1,
                content_2="1",
                content_4=tab23_content_4,
            )

        if data["wallboxVorh"]:
            self.line(self.l_margin, self.get_y() + 5, 196.5, self.get_y() + 5)
            self.set_y(self.get_y() + 10)

            # WALLBOX
            wallbox_1 = self.get_attribute_by_identifier("wallbox_1", "content")
            self.setup_text("wallbox_1", wallbox_1, bold=True, alignment="L")
            wallbox_2 = self.get_attribute_by_identifier("wallbox_2", "content")
            self.setup_text("wallbox_2", wallbox_2, alignment="L")

            eintrag += 1
            tab24_eintrag_nummer = str(eintrag) + "."
            tab24_content_1 = str(data["wallboxTyp"])
            tab24_content_2 = str(data["wallboxAnz"])
            tab24_content_4 =  str(data["wallboxText"])
            self.setup_eintrag_text(
                "wallbox_typ",
                tab24_eintrag_nummer,
                content_1=tab24_content_1,
                content_2=tab24_content_2,
                content_4=tab24_content_4,
            )

        # OPTIONALES ZUBEHÖR
        global zubehoerLimitMitWallbox, zubehoerLimitOhneWallbox
        if zubehoerVorhanden:
            self.line(self.l_margin, self.get_y() + 5, 196.5, self.get_y() + 5)
            self.set_y(self.get_y() + 10)

            optionales_zubehoer_1 = self.get_attribute_by_identifier(
                "optionales_zubehoer_1", "content"
            )
            self.setup_text(
                "optionales_zubehoer_1", optionales_zubehoer_1, bold=True, alignment="L"
            )
            optionales_zubehoer_2 = self.get_attribute_by_identifier(
                "optionales_zubehoer_2", "content"
            )
            self.setup_text(
                "optionales_zubehoer_2", optionales_zubehoer_2, alignment="L"
            )

        if data["thor"] == True:
            eintrag += 1
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["thorName"])
            tab28_content_2 = "1 Stk."
            tab28_content_4 = str(data["thorText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_2=tab28_content_2,
                content_4=tab28_content_4,
            )
        if data["midZaehler"] > 0:
            eintrag += 1
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["midZaehlerName"])
            tab28_content_2 = str(data["midZaehler"]) + " Stk."
            tab28_content_4 = str(data["midZaehlerText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_2=tab28_content_2,
                content_4=tab28_content_4,
            )
        if data["apzFeld"] == True:
            eintrag += 1
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["apzFeldName"])
            tab28_content_2 = "1 Stk."
            tab28_content_4 = str(data["apzFeldText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_2=tab28_content_2,
                content_4=tab28_content_4,
            )
        if data["zaehlerschrank"] == True:
            eintrag += 1
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["zaehlerschrankName"])
            tab28_content_2 = "1 Stk."
            tab28_content_4 = str(data["zaehlerschrankText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_2=tab28_content_2,
                content_4=tab28_content_4,
            )
        if data["potenzialausgleich"] == True:
            eintrag += 1
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["potenzialausgleichName"])
            tab28_content_2 = "1 Stk."
            tab28_content_4 = str(data["potenzialausgleichText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_2=tab28_content_2,
                content_4=tab28_content_4,
            )
        # Zubehör mit Herstellerbezug
        if data["hersteller"] == "Huawei":
            # OPTIMIERER HUAWEI
            if data["anzOptimierer"] > 0:

                eintrag += 1
                tab25_eintrag_nummer = str(eintrag) + "."
                tab25_content_1 = self.get_attribute_by_identifier(
                    "optimierer_huawei_1", "content"
                )
                tab25_content_2 = str(data["anzOptimierer"]) + " Stk."
                tab25_content_4 = self.get_attribute_by_identifier(
                    "optimierer_huawei_2", "content"
                )
                self.setup_eintrag_text(
                    "optimierer_huawei_2",
                    tab25_eintrag_nummer,
                    tab25_content_1,
                    content_2=tab25_content_2,
                    content_4=tab25_content_4,
                )

            # NOTSTROM
            if data["notstrom"]:
                eintrag += 1
                tab26_eintrag_nummer = str(eintrag) + "."
                tab26_content_1 = self.get_attribute_by_identifier(
                    "notstrom_huawei_1", "content"
                )
                tab26_content_2 = "1 Stk."
                tab26_content_4 = self.get_attribute_by_identifier(
                    "notstrom_huawei_2", "content"
                )
                self.setup_eintrag_text(
                    "notstrom_huawei_2",
                    tab26_eintrag_nummer,
                    tab26_content_1,
                    content_2=tab26_content_2,
                    content_4=tab26_content_4,
                )

            # WANDHALTERUNG
            if data["anzWandhalterungSpeicher"] > 0:

                # Tabelle Eintrag Wandhalterung
                eintrag += 1
                tab27_eintrag_nummer = str(eintrag) + "."
                tab27_content_1 = self.get_attribute_by_identifier(
                    "wandhalterung_huawei_1", "content"
                )
                tab27_content_2 = str(data["anzWandhalterungSpeicher"]) + " Stk."

                self.setup_eintrag_text(
                    "wandhalterung_huawei_1",
                    tab27_eintrag_nummer,
                    tab27_content_1,
                    content_2=tab27_content_2,
                )

            # HUAWEI ELWA
            if data["elwa"] == True:
                eintrag += 1
                tab29_eintrag_nummer = str(eintrag) + "."
                tab29_content_1 = str(data["elwaName"])
                tab29_content_2 = "1 Stk."
                tab29_content_4 = str(data["elwaText"])
                self.setup_eintrag_text(
                    "zubehoer_platzhalter",
                    tab29_eintrag_nummer,
                    tab29_content_1,
                    content_2=tab29_content_2,
                    content_4=tab29_content_4,
                )

        if data["hersteller"] == "Viessmann":

            # OPTIMIERER VIESSMANN
            if data["anzOptimierer"] > 0:
                eintrag += 1
                tab25_eintrag_nummer = str(eintrag) + "."
                tab25_content_1 = self.get_attribute_by_identifier(
                    "optimierer_viessmann_1", "content"
                )
                tab25_content_2 = str(data["anzOptimierer"]) + " Stk."
                tab25_content_4 = self.get_attribute_by_identifier(
                    "optimierer_viessmann_2", "content"
                )
                self.setup_eintrag_text(
                    "optimierer_viessmann_2",
                    tab25_eintrag_nummer,
                    tab25_content_1,
                    content_2=tab25_content_2,
                    content_4=tab25_content_4,
                )

                eintrag += 1
                tab26_eintrag_nummer = str(eintrag) + "."
                tab26_content_1 = self.get_attribute_by_identifier(
                    "optimierer_viessmann_3", "content"
                )
                tab26_content_2 = "1 Stk."
                tab26_content_4 = self.get_attribute_by_identifier(
                    "optimierer_viessmann_4", "content"
                )
                self.setup_eintrag_text(
                    "optimierer_viessmann_4",
                    tab26_eintrag_nummer,
                    tab26_content_1,
                    content_2=tab26_content_2,
                    content_4=tab26_content_4,
                )

                eintrag += 1
                tab27_eintrag_nummer = str(eintrag) + "."
                tab27_content_1 = self.get_attribute_by_identifier(
                    "optimierer_viessmann_5", "content"
                )
                tab27_content_2 = "1 Stk."

                self.setup_eintrag_text(
                    "optimierer_viessmann_5",
                    tab27_eintrag_nummer,
                    tab27_content_1,
                    content_2=tab27_content_2,
                )

            if data["notstrom"]:

                eintrag += 1
                tab28_eintrag_nummer = str(eintrag) + "."
                tab28_content_1 = self.get_attribute_by_identifier(
                    "notstrom_viessmann_1", "content"
                )
                tab28_content_2 = "1 Stk."
                tab28_content_4 = self.get_attribute_by_identifier(
                    "notstrom_viessmann_2", "content"
                )
                self.setup_eintrag_text(
                    "notstrom_viessmann_2",
                    tab28_eintrag_nummer,
                    tab28_content_1,
                    content_2=tab28_content_2,
                    content_4=tab28_content_4,
                )

            # GRIDBOX
            if data["wallboxAnz"] >= 2:

                eintrag += 1
                tab29_eintrag_nummer = str(eintrag) + "."
                tab29_content_1 = self.get_attribute_by_identifier(
                    "gridbox_viessmann_1", "content"
                )
                tab29_content_2 = "1 Stk."
                tab29_content_4 = self.get_attribute_by_identifier(
                    "gridbox_viessmann_2", "content"
                )
                self.setup_eintrag_text(
                    "gridbox_viessmann_2",
                    tab29_eintrag_nummer,
                    tab29_content_1,
                    content_2=tab29_content_2,
                    content_4=tab29_content_4,
                )
        addedPage = False
        if data["betaPlatte"] == True:
            eintrag += 1
            if not addedPage and ((data["wallboxAnz"] > 0 and eintrag > zubehoerLimitMitWallbox) or eintrag > zubehoerLimitOhneWallbox):
                self.add_page()
                addedPage = True
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["betaPlatteName"])
            tab28_content_4 = str(data["betaPlatteText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_4=tab28_content_4,
            )
        if data["metallZiegel"] == True:
            eintrag += 1
            if not addedPage and ((data["wallboxAnz"] > 0 and eintrag > zubehoerLimitMitWallbox) or eintrag > zubehoerLimitOhneWallbox):
                self.add_page()
                addedPage = True
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["metallZiegelName"])
            tab28_content_4 = str(data["metallZiegelText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_4=tab28_content_4,
            )
        if data["geruestKunde"] == True:
            eintrag += 1
            if not addedPage and ((data["wallboxAnz"] > 0 and eintrag > zubehoerLimitMitWallbox) or eintrag > zubehoerLimitOhneWallbox):
                self.add_page()
                addedPage = True
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["geruestKundeName"])
            tab28_content_2 = "1"
            tab28_content_4 = str(data["geruestKundeText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_2=tab28_content_2,
                content_4=tab28_content_4,
            )

        if data["dachhakenKunde"] == True:
            eintrag += 1
            if not addedPage and ((data["wallboxAnz"] > 0 and eintrag > zubehoerLimitMitWallbox) or eintrag > zubehoerLimitOhneWallbox):
                self.add_page()
                addedPage = True
            tab28_eintrag_nummer = str(eintrag) + "."
            tab28_content_1 = str(data["dachhakenKundeName"])
            tab28_content_2 = "1"
            tab28_content_4 = str(data["dachhakenKundeText"])
            self.setup_eintrag_text(
                "zubehoer_platzhalter",
                tab28_eintrag_nummer,
                tab28_content_1,
                content_2=tab28_content_2,
                content_4=tab28_content_4,
            )
        return eintrag

    def pricePage(self, data):
        self.add_page()
        self.is_last_page = False
        # Angebotssumme
        self.set_fill_color(240)
        self.set_y(35)
        self.set_font("JUNO Solar Lt", "B", 17)
        self.multi_cell(0, 6, "Angebotssumme\n ", 0, "L", fill=True)
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
        sum = data["kostenPVA"]
        netto = convertCurrency("{:,.2f} €".format(sum))
        mwst = convertCurrency("{:,.2f} €".format(sum * steuer))
        brutto = convertCurrency("{:,.2f} €".format(sum * (1 + steuer)))
        self.multi_cell(0, 6, f'{str(data["kWp"])} kWp\n \n{netto}\n{mwst}', 0, "R")
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
        # Zahlungsmodalitäten
        y = self.get_y()
        self.set_y(y + 5)
        self.set_font("JUNO Solar Lt", "B", 12)
        # zahlungsmodalitäten
        self.cell(0, 6, "Zahlungsmodalitäten", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y + 11)
        if data["zahlungs_bedingungen"]:
            if data["zahlungs_bedingungen"] == "20 – 70 – 10 %":
                # zahlungsmodalitäten_1
                self.multi_cell(
                    0,
                    6,
                    "0% bei Angebotsannahme\n20% bei Auftragsbestätigung\n70% bei Baubeginn\n10% bei Netzanschluss",
                    0,
                    0,
                    "L",
                )  # type: ignore
            elif data["zahlungs_bedingungen"] == "10 – 80 – 10 %":
                # zahlungsmodalitäten_2
                self.multi_cell(
                    0,
                    6,
                    "0% bei Angebotsannahme\n10% bei Auftragsbestätigung\n80% bei Baubeginn\n10% bei Netzanschluss",
                    0,
                    0,
                    "L",
                )  # type: ignore
            elif data["zahlungs_bedingungen"] == "100 – 0 – 0 %":
                # zahlungsmodalitäten_3
                self.multi_cell(
                    0,
                    6,
                    "0% bei Angebotsannahme\n100% bei Auftragsbestätigung\n0% bei Baubeginn\n0% bei Netzanschluss",
                    0,
                    0,
                    "L",
                )
        else:
            self.multi_cell(0, 6, "20% bei Auftragsbestätigung\n70% bei Baubeginn\n10% bei Netzanschluss", 0, 0, "L")  # type: ignore
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

    def agbPage(self):
        self.skip_logo = True
        self.add_page()
        self.is_last_page = True
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

    def certPage(self, certifikate):
        if certifikate:
            self.add_page()
            self.is_last_page = True
            self.image(
                certifikate.path,
                x=5,
                y=10,
                w=198,
            )
        else:
            pass

    def financePage(self, data):
        if data["finanzierung"]:
            self.add_page()
            finanzierung_0 = self.get_attribute_by_identifier("finanzierung_0", "content")
            self.setup_text("finanzierung_0", finanzierung_0, bold=True, alignment="L")
            finanzierung_1 = self.get_attribute_by_identifier("finanzierung_1", "content")
            self.setup_text("finanzierung_1", finanzierung_1, bold=True, alignment="L")
            finanzierung_2 = self.get_attribute_by_identifier("finanzierung_2", "content")
            self.setup_text("finanzierung_2", finanzierung_2, alignment="L")
            finanzierung_3 = self.get_attribute_by_identifier("finanzierung_3", "content")
            self.setup_text("finanzierung_3", finanzierung_3, alignment="L")
            finanzierung_4 = self.get_attribute_by_identifier("finanzierung_4", "content")
            self.setup_text("finanzierung_4", finanzierung_4, bold=True, alignment="L")
            finanzierung_5 = self.get_attribute_by_identifier("finanzierung_5", "content")
            self.setup_text("finanzierung_5", finanzierung_5, alignment="L")
            finanzierung_6 = self.get_attribute_by_identifier("finanzierung_6", "content")
            self.setup_text("finanzierung_6", finanzierung_6, bold=True, alignment="L")
            finanzierung_7 = self.get_attribute_by_identifier("finanzierung_7", "content")
            self.setup_text("finanzierung_7", finanzierung_7, alignment="L")
            finanzierung_8 = self.get_attribute_by_identifier("finanzierung_8", "content")
            self.setup_text("finanzierung_8", finanzierung_8, bold=True, alignment="L")
            finanzierung_9 = self.get_attribute_by_identifier("finanzierung_9", "content")
            self.setup_text("finanzierung_9", finanzierung_9, alignment="L")

            self.set_fill_color(240)
            self.set_y(125)
            self.set_font("JUNO Solar Lt", "B", 17)
            self.multi_cell(0, 6, "Ihre Investition\n ", 0, "L", fill=True)
            self.set_font("JUNO Solar Lt", "", 12)
            self.set_y(135)
            steuer = data["steuersatz"]
            self.multi_cell(
                0,
                6,
                "Barzahlungspreis\nAnzahlung\nNettokreditbetrag\nMonatliche Rate\nLaufzeit\nSollzinssatz\nEffektiver Jahreszins\nGesamtkreditbetrag",
                0,
                "L",
                fill=True,
            )
            self.set_y(135)
            barzahlung = convertCurrency("{:,.2f} €".format(data["kostenPVA"]))
            anzahlung = convertCurrency("{:,.2f} €".format(data["anzahlung"]))
            nettoKr = convertCurrency("{:,.2f} €".format(data["nettokreditbetrag"]))
            monatlicheRate = convertCurrency("{:,.2f} €".format(data["monatliche_rate"]))
            laufzeit = str(data["laufzeit"]) + " Monate"
            sollzinssatz = str(data["sollzinssatz"]) + "%"
            effektiverJ = str(data["effektiver_zins"]) + "%"
            gesamtkr = convertCurrency("{:,.2f} €".format(data["gesamtkreditbetrag"]))
            self.multi_cell(0, 6, f'{barzahlung}\n{anzahlung}\n{nettoKr}\n{monatlicheRate}\n{laufzeit}\n{sollzinssatz}\n{effektiverJ}', 0, "R")
            self.set_y(177)
            self.set_font("JUNO Solar Lt", "B", 12)
            self.cell(0, 6, gesamtkr, 0, 0, "R")
            self.line(175, 177, 197, 177)
        else:
            pass


def replace_spaces_with_underscores(s: str) -> str:
    return s.replace(" ", "_").replace(",","")


def anzahlZubehoer(data):
    anzahlZubehoer = 0
    if data["optionVorh"]:
        anzahlZubehoer += 1
    if data["elwa"]:
        anzahlZubehoer += 1
    if data["thor"]:
        anzahlZubehoer += 1
    if data["apzFeld"]:
        anzahlZubehoer += 1
    if data["zaehlerschrank"]:
        anzahlZubehoer += 1
    if data["potenzialausgleich"]:
        anzahlZubehoer += 1
    if data["geruestKunde"]:
        anzahlZubehoer += 1
    if data["dachhakenKunde"]:
        anzahlZubehoer += 1
    if data["anzOptimierer"] > 0:
        anzahlZubehoer += 1
    if data["midZaehler"] > 0:
        anzahlZubehoer += 1
    if data["betaPlatte"]:
        anzahlZubehoer += 1
    if data["metallZiegel"]:
        anzahlZubehoer += 1
    return anzahlZubehoer

def createOfferPdf(data, vertrieb_angebot, certifikate, user, withCalc=False):
    global title, pages, zubehoerLimitMitWallbox, zubehoerLimitOhneWallbox
    title1 = f"{vertrieb_angebot.angebot_id}"
    pages = 6
    zubehoerLimitMitWallbox = 31
    zubehoerLimitOhneWallbox = 34
    if certifikate:
        pages += 1
    if data["finanzierung"]:
        pages += 1
    if withCalc:
        pages += 2
    anzZubehoer = anzahlZubehoer(data)
    if (data["wallboxAnz"] > 0 and anzZubehoer > zubehoerLimitMitWallbox - 24) or anzZubehoer > zubehoerLimitOhneWallbox - 23:
        pages += 1
    if anzZubehoer > 0 or data["wallboxVorh"] or data["kWp"] >= 25.0:
        pages += 1

    pdf = PDF(title1)
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")
    pdf.set_creator(f"{user.first_name} {user.last_name})")
    # create the offer-PDF
    eintrag = 0
    eintrag = pdf.page1(data, eintrag)
    eintrag = pdf.page2(data, eintrag)
    eintrag = pdf.page3(data, eintrag)
    eintrag = pdf.page4(data, eintrag)

    pdf.pricePage(data)
    pdf.financePage(data)
    pdf.certPage(certifikate)
    pdf.agbPage()

    if withCalc:
        user_folder = os.path.join(
            settings.MEDIA_ROOT, f"pdf/usersangebots/{user.username}/Kalkulationen/"
        )
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        pdf = calcPage1(pdf, data)
        pdf = calcPage2(pdf, data, user_folder, vertrieb_angebot)

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content
