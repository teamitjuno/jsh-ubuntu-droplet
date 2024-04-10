from math import ceil
from datetime import datetime, date
from fpdf import FPDF
from config import settings
from vertrieb_interface.pdf_services.helper_functions import convertCurrency
import os

title = ""
pages = "6"


class PDF(FPDF):
    def __init__(self, title1, *args, **kwargs):
        super(PDF, self).__init__(*args, **kwargs)
        self.is_last_page = False
        self.title1 = title1
        self.set_left_margin(18.875)
        self.set_right_margin(12.875)

    def header(self):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)

        # Position at 1.5 cm from bottom
        self.set_y(0)
        self.set_font("JUNO Solar Lt", "", 8)
        self.set_text_color(0)
        self.cell(
            0, 10, f"Seite {str(self.page_no())}/{pages}   {self.title1}", 0, 0, ""
        )
        if not self.is_last_page:
            font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
            self.add_font("JUNO Solar Lt", "", font_path, uni=True)
            font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
            self.add_font("JUNO Solar Lt", "B", font_path, uni=True)

            self.set_y(15)
            self.set_font("JUNO Solar Lt", "", 12)
            self.set_text_color(0)
            # Page number
            # self.cell(0, 10, f"Seite {str(self.page_no())}/{pages}", 0, 0, "")
            self.set_x(40)
            if self.page_no() != 1:
                self.cell(0, 10, title, 0, 0, "")
            self.image(
                os.path.join(settings.MEDIA_ROOT, "fonts/junosolar_logo.jpg"),
                x=167,
                y=10,
                w=30,
                h=15,
            )
            self.ln(15)

    def footer(self):
        if not self.is_last_page:
            # Arial italic 8
            self.set_font("JUNO Solar Lt", "", 8)
            self.set_text_color(128)
            self.set_y(-25)
            self.set_x(25)
            self.multi_cell(0, 3, "Amtsgericht Chemnitz\nHR-Nr.:HRB 34192\nUSt.-ID: DE345149530\nSteuer-Nr.:227/156/19508\nGeschäftsführung: Denny Schädlich", 0, 0, "")  # type: ignorehttp://127.0.0.1:8000/vertrieb/home/
            self.set_y(-25)
            self.set_x(85)
            centered_text1 = "Commerzbank Chemnitz\nIBAN: DE94 8704 0000 0770 0909 00\nBIC: COBADEFFXXX"
            self.multi_cell(0, 3, centered_text1, 0, "")
            self.set_y(-25)
            self.set_x(150)
            centered_text1 = "Volksbank Chemnitz\nIBAN: DE51 8709 6214 0321 1008 13\nBIC: GENODEF1CH1"
            self.multi_cell(0, 3, centered_text1, 0, "")

    def page1(self, data, eintrag):
        self.add_page()
        # Adresszeile
        self.set_font("JUNO Solar Lt", "", 8)
        self.set_text_color(128)
        self.cell(
            0,
            10,
            "JUNO SOLAR Home GmbH & Co. KG ∙ Ziegelstraße 1a ∙ D-08412 Werdau",
            0,
            0,
            "",
        )

        self.ln(15)
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_text_color(0)
        self.multi_cell(0, 5, f'{data["firma"]}\n{data["anrede"]} {data["kunde"]}\n{data["adresse"]}', 0, 0, "L")  # type: ignore
        # self.line(18,65,80,65) #unter Adresse
        self.set_font("JUNO Solar Lt", "B", 11)
        self.set_x(130)
        self.set_y(33)
        self.multi_cell(
            0,
            5,
            "JUNO SOLAR Home GmbH & Co. KG",
            0,
            "R",
        )
        self.set_x(130)
        self.set_y(38)
        self.set_font("JUNO Solar Lt", "", 11)
        self.multi_cell(
            0,
            5,
            "Ziegelstraße 1a\nD-08412 Werdau",
            0,
            "R",
        )
        self.set_x(130)
        self.set_y(53)
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_text_color(0)

        self.multi_cell(
            0,
            5,
            data["vertriebler"],
            0,
            "R",
        )
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(63)
        self.set_x(130)
        self.multi_cell(
            0,
            5,
            f'\nDatum: {date.today().strftime("%d.%m.%Y")}\nwww.juno-solar.com',
            0,
            "R",
        )
        self.set_y(80)
        self.set_font("JUNO Solar Lt", "B", 17)
        self.cell(0, 6, title, 0, 0, "R")
        # Überschrift und Text
        self.set_font("JUNO Solar Lt", "B", 14)
        self.set_x(0)
        self.set_y(80)
        self.cell(0, 6, "ANGEBOT", 0, 0, "L")
        self.set_x(0)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, f"{self.title1}", 0, 0, "R")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_x(0)
        self.set_y(90)
        self.multi_cell(0, 5, "Gesamtleistung der Anlage:\nStandort der Anlage:", 0, "")
        self.set_y(90)
        self.set_x(70)
        self.multi_cell(0, 5, f'{str(data["kWp"])} kWp\n{data["standort"]}', 0, "L")
        self.set_y(105)
        if "Firma" in data["anrede"]:
            self.cell(0, 6, f"Sehr geehrte Damen und Herren", 0, 0, "L")
        elif "Familie" in data["anrede"]:
            self.cell(0, 6, f"Sehr geehrte Damen und Herren", 0, 0, "L")
        else:
            self.cell(
                0, 6, f'Sehr geehrte {data["anrede"]} {data["kunde"]},', 0, 0, "L"
            )
        self.set_x(0)
        self.set_y(115)
        self.multi_cell(
            0,
            5,
            "vielen Dank für Ihre Anfrage. Wir  bieten  Ihnen  hiermit  die  komplette  Lieferung  und  Montage folgender Photovoltaikanlage an:",
            0,
            "",
        )
        # Tabelle Beginn
        self.set_font("JUNO Solar Lt", "B", 10)
        self.set_x(0)
        self.set_y(130)
        self.cell(0, 6, "Pos.", 0, 0, "L")
        self.set_x(37)
        self.cell(0, 6, "Bezeichnung", 0, 0, "L")
        self.set_x(150)
        self.cell(0, 6, "Menge", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "Gesamtpreis", 0, 0, "R")
        # Gleichstromseitige Installation
        self.line(18, 135, 196, 135)
        self.set_y(139)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Bestandteile Photovoltaikanlage", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(140)
        self.multi_cell(
            0,
            5,
            "\nDie nachfolgenden Positionen beinhalten die Hardware, bzw. Kompontenten der angebotenen Photovoltaikanlage:",
            0,
            "L",
        )
        # Tabelle Eintrag 1

        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(155)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, data["module"], 0, 0, "L")
        self.set_y(160)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            f'∙ Leistung pro Modul: {data["wpModule"]} Wp\n∙ Produktgarantie: {data["produktGarantie"]}\n∙ Leistungsgarantie: {data["leistungsGarantie"]}',
            0,
            "L",
        )
        self.set_y(155)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, f'{str(data["anzModule"])} Stk', 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        if data["hersteller"] == "Viessmann":
            # Tabelle Eintrag 2
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(180)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 5, "Viessmann Vitocharge VX3", 0, 0, "L")
            self.set_y(185)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(
                0,
                5,
                "∙ Modell nach Auslegung\n∙ inkl. Energie-Management\n∙ inkl. externen Überspannungsschutz AC/DC\n∙ Produktgarantie: "
                + data["garantieJahre"],
                0,
                "L",
            )
            self.set_y(180)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.cell(0, 6, "nach Auslegung", 0, 0, "L")
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")
            # Tabelle Eintrag 3
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(210)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 5, "Viessman Energiezähler", 0, 0, "L")
            self.set_y(215)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(
                0,
                5,
                "∙ Smart-Meter zur Strommessung im Haushalt\n∙ Produktgarantie: 2 Jahre",
                0,
                "L",
            )
            self.set_y(210)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.cell(0, 6, "nach Auslegung", 0, 0, "L")
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")
            # Tabelle Eintrag 4
            if data["batterieVorh"]:
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(230)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 5, "Batteriespeicher: Viessmann Vitocharge VX3", 0, 0, "L")
                self.set_y(235)
                self.set_x(25)
                self.cell(0, 5, "Batteriemodule (je 5 kWh)", 0, 0, "L")
                self.set_y(240)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ max. Lade-/Entladeleistung:5 kW \n∙ Produktgarantie: 10 Jahre",
                    0,
                    "L",
                )
                self.set_y(230)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, str(data["batterieAnz"]), 0, 0, "L")  # type: ignore
                self.set_x(170)
                self.set_y(230)
                self.cell(0, 6, "inklusive", 0, 0, "R")

        elif data["hersteller"] == "Huawei":
            # Tabelle Eintrag 2
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(180)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 5, "Wechselrichter Huawei SUN2000", 0, 0, "L")
            self.set_y(185)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(
                0,
                5,
                "∙ Modell nach Auslegung\n∙ inkl. Smart Dongle Wlan + Ethernet\n∙ inkl. Überspannungsschutz AC/DC\n∙ Produktgarantie: "
                + data["garantieJahre"],
                0,
                "L",
            )
            self.set_y(180)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.cell(0, 6, "nach Auslegung", 0, 0, "L")
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")

            # Tabelle Eintrag 3
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(210)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 5, "Huawei Smart Power Sensor DTSU666H", 0, 0, "L")
            self.set_y(215)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(
                0,
                5,
                "∙ Smart-Meter zur Strommessung im Haushalt\n∙ Produktgarantie: 2 Jahre",
                0,
                "L",
            )
            self.set_y(210)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.cell(0, 6, "nach Auslegung", 0, 0, "L")
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")

            # Tabelle Eintrag 4
            if data["batterieVorh"]:
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(230)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 5, "Batteriespeicher: Huawei LUNA 2000", 0, 0, "L")
                self.set_y(235)
                self.set_x(25)
                self.multi_cell(
                    0, 5, "Leistungsmodule\nBatteriemodule (je 5 kWh)", 0, 0, "L"
                )
                self.set_y(245)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ max. Lade-/Entladeleistung: 5 kW\n∙ Produktgarantie: 10 Jahre",
                    0,
                    "L",
                )
                self.set_y(230)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, str(data["batterieAnz"]), 0, 0, "L")  # type: ignore
                self.set_x(170)
                self.set_y(230)
                self.cell(0, 6, "inklusive", 0, 0, "R")
        return eintrag

    def page2(self, data, eintrag):
        self.add_page()
        y = 30

        # Tabelle Eintrag 5
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, "Unterkonstruktion", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(0, 5, "Hersteller: S:FLEX oder gleichwertig", 0, "L")
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(50)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 15
        # Tabelle Eintrag 6
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, "Solarleitung", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Solarkabel 2-fach isoliert, UV-beständig, Leitungsverlust DC unter 1%",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(50)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 15
        # Tabelle Eintrag 7
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, "Stecker und Buchsen", 0, 0, "L")
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(50)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 10
        # Tabelle Eintrag 8
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, "Kabelkanäle", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "∙ Ausführung Außenbereich: Zink\n∙ Ausführung Innenbereich: Kunststoff",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(50)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 25

        # Gleichstromseitige Installation
        self.line(18, y - 4, 200, y - 4)
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Gleichstromseitige Installation", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        y += 5
        self.set_y(y)
        self.multi_cell(
            0,
            5,
            "Die gleichstromseitige Installation umfasst alle Arbeiten im Gleichstromkreis der Photovoltaikanlage. Der Wechselrichter ist der Schnittpunkt zur wechselstromseitegen Installation.",
            0,
            "L",
        )
        y += 15

        # Tabelle Eintrag 9
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "DC-Installation", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Gleichstrom-Elektroinstallation: Montage und Verlegung der\nModul-Unterkonstruktion sowie Solarmodule bis zu den Wechselrichtern.",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 20
        # Tabelle Eintrag 10
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Potentialausgleich", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Der Potentialausgleich ist in DIN VDE 0100, Teil 540 festgelegt. \nEr dient der Erdung der PV-Anlage und erfolgt nach\nDIN EN 50083-1 (VDE 0855-1).",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 25
        # Tabelle Eintrag 11
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Gerüst zur Absturzsicherung", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0, 5, "Gerüst wird entsprechend der Anfonderung vor Ort gewählt", 0, "L"
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 20
        # Wechselstromseitige Installation und Inbetriebnahme
        self.line(18, y - 4, 200, y - 4)
        self.set_y(y - 1)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(
            0, 6, "Wechselstromseitige Installation und Inbetriebnahme", 0, 0, "L"
        )
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        self.multi_cell(
            0,
            5,
            "\nDie wechselstromseitige Installation beschreibt sämtliche Bauteile sowie Dienstleistungen, die sich im Wechselstromkreis befinden. Die Installation des Wechselrichters stellt hierbei den Schnittpunkt zur gleichstromseitigen Installation dar. Kundenseitig stellt der Zählerschrank bzw. die Übergabestation die Schnittstelle zum Energieversorger",
            0,
            "L",
        )
        y += 25
        # Tabelle Eintrag 12
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "AC-Installation", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0, 5, "Kupferleitung, Leitungsquerschnitt entsprechend AC-Leitung", 0, "L"
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 15

        # Tabelle Eintrag 13
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Netzanschluss", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(0, 5, "an den vorhanden Hausanschlusskasten", 0, "L")
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 15

        # Tabelle Eintrag 14
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(
            0, 6, "Installation und Parametrierung des Wechselrichters", 0, 0, "L"
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 15

        self.line(18, y - 4, 200, y - 4)
        return eintrag

    def page3(self, data, eintrag):
        self.add_page()
        # Anlagenüberwachung und Visualisierung
        y = 25
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Anlagenüberwachung und Visualisierung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y + 5)
        self.multi_cell(
            0,
            5,
            "\nDiese Position beschreibt die technischen Bauteile und deren Installation, um eine Anlagenüberwachung und die Visualisierung der Ertragsdaten zu realisieren bzw. darzustellen.",
            0,
            "L",
        )
        y += 25
        # Tabelle Eintrag 15

        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "Integriertes Monitoring zur Anlagenüberwachung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 10)
        self.set_y(y + 5)
        self.set_x(25)
        self.multi_cell(
            0,
            5,
            "mittels Viessmann ViCare App\nkompatibel mit Android und iOS",
            0,
            0,
            "L",
        )
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        if not data["hersteller"]:
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(
                0,
                5,
                "mittels Huawei FusionSolar App\nkompatibel mit Android und iOS",
                0,
                "L",
            )

        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        y += 25
        # Netzanschlussmanagement
        self.line(18, y - 4, 200, y - 4)
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Netzanschlussmanagement", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        self.multi_cell(
            0,
            5,
            "\nVon der Einspeiseanfrage bis hin zur Inbetriebnahme der PV-Anlage, unser Netzanschlussmanagement bearbeitet für Sie alle Formalitäten, die der VNB vom Anlagenbetreiber zum Beantragen seines Anschlussbegehrens fordert, unter Berücksichtung öffentlich- und privatrechlicher Vorschriften.",
            0,
            "L",
        )
        y += 25
        # Tabelle Eintrag 16
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Anmeldung zum Netzanschluss", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Mit der Anmeldung zum Netzanschluss wird dem örtlichen Netzbetreiber das\nNetzanschlussbegehren des Anlagenbetreibers übermittelt.",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 20

        # Tabelle Eintrag 17
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "EEG-Fertigmeldung und -Inbetriebnahme", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0, 5, "Die Fertigmeldung erfolgt nach erfolgreichem Bauabschluss.", 0, "L"
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        y += 15
        # Tabelle Eintrag 18
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Registrierung im Marktstammdatenregister", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Die Registrierung im Marktstammdatenregister ist verpflichtend und muss\nspätestens vier Wochen nach der EEG-Fertigmeldung erfolgen.",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        y += 20

        # Tabelle Eintrag 19
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Antrag zum Zählerwechsel", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "∙ Der Einbau des Zweirichtungszähler erfolgt durch\nden zuständigen Messstellenbetreiber (Falls kein\nZweirichtungszähler vorhanden ist).\n∙ Evtl anfallende Kosten durch den Netzbetreiber\nsind vom Auftragnehmer zu tragen.",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        y += 35

        # Tabelle Eintrag 20
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Bestellung FRE (bei Modulleistung ≥ 25 kWp)", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "∙ Der Einbau des FRE (Funk-Rundsteuerempfänger) erfolgt\nkostenfrei durch den Auftraggeber.\n∙ Anfallende Kosten durch den Netzbetreiber\nsind vom Auftragnehmer zu tragen.",
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        y = 140
        y += 45
        self.line(18, y + 35, 200, y + 35)

        #
        # Zusätzliche Leistungen

        self.set_y(y + 40)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Zusätzliche Leistungen", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y + 50)
        self.multi_cell(
            0,
            5,
            "Die folgenden inkludierten Leistungen umfassen alles Notwendige, damit Sie sich um nichts Weiteres kümmern müssen. Wir sorgen für alles, von der Planung bis zum Aufräumen nach erfolgreicher Arbeit.",
            0,
            "L",
        )

        # Tabelle Eintrag 21
        y += 60
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y + 5)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Frachtkosten", 0, 0, "L")
        self.set_y(y + 10)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Die Frachtkosten beziehen sich auf die alle Materialien/Komponenten",
            0,
            "L",
        )
        self.set_y(y + 5)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        return eintrag

    def page4(self, data, eintrag):
        self.add_page()
        y = 25

        # Tabelle Eintrag 22
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Müllentsorgung", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Nach Fertigstellung werden sämtliche Reste an\nBaumaterialien und Abfällen beseitigt.",
            0,
            "L",
        )
        self.set_y(y + 5)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        y += 20

        # Tabelle Eintrag 22
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Planung", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "komplette Anlagenplanung (Stringplanung) inkl. Dokumentation.",
            0,
            "L",
        )
        self.set_y(y + 5)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")

        y += 15
        # WALLBOX
        if data["wallboxVorh"]:
            if data["hersteller"] == "Huawei":

                self.line(18, y, 200, y)
                self.set_y(y + 5)
                self.set_font("JUNO Solar Lt", "B", 12)
                self.cell(0, 6, "Ladestation für E-Fahrzeug (Wallbox)", 0, 0, "L")
                self.set_y(y + 10)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, "Mit einer Wallbox können Sie die Energie Ihrer Photovoltaikanlage zum Laden Ihres Elektrofahrzeugs nutzen. Eine intelligente Steuerung (opt. Zubehör) kann den Ladestrom kontinuierlich der aktuellen Energieerzeugung anpassen.", 0, 0, "L")  # type: ignore
                # Tabelle Eintrag 2X
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y + 25)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Huawei Fusion Charge AC", 0, 0, "L")
                self.set_y(y + 30)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "∙ inkl. Lade- und Lastmanagement\n∙ maximale Ladeleistung: 22 kW\n∙ Parametrierbar auf 11 kW (für KfW Förderung)\n∙ Produktgarantie: 3 Jahre",
                    0,
                    0,
                    "L",
                )
                self.set_y(y + 25)
                self.set_x(25)
                # self.set_font('JUNO Solar Lt', '', 10)
                self.multi_cell(0, 5, data["wallboxText"], 0, "L")
                self.set_y(y + 25)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, str(data["wallboxAnz"]), 0, "L")
                self.set_y(y + 25)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")

                y += 40

            elif data["hersteller"] == "Viessmann":

                self.line(18, y, 200, y)
                self.set_y(y + 5)
                self.set_font("JUNO Solar Lt", "B", 12)
                self.cell(0, 6, "Ladestation für E-Fahrzeug (Wallbox)", 0, 0, "L")
                self.set_y(y + 10)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, "Mit einer Wallbox können Sie die Energie Ihrer Photovoltaikanlage zum Laden Ihres Elektrofahrzeugs nutzen. Eine intelligente Steuerung (opt. Zubehör) kann den Ladestrom kontinuierlich der aktuellen Energieerzeugung anpassen.", 0, 0, "L")  # type: ignore
                # Tabelle Eintrag 2X
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y + 25)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Viessmann Charging Station", 0, 0, "L")
                self.set_y(y + 30)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    6,
                    "∙ inkl Lade- und Lastmanagement\n∙ maximale Ladeleistung: 11 kW\n∙ inkl Ladekabel mit 7,5 m Kabellänge\n∙ Produktgarantie: 2 Jahre",
                    0,
                    0,
                    "L",
                )
                self.set_y(y + 25)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, str(data["wallboxAnz"]), 0, "L")
                self.set_y(y + 25)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 20

        y += 10
        # OPTIONALES ZUBEHÖR
        if (
            not data["optionVorh"]
            and not data["elwa"]
            and not data["thor"]
            and not data["anzOptimierer"] > 0
        ):
            self.line(18, y, 200, y)
        else:
            y += 5
            self.line(18, y, 200, y)
            self.set_y(y + 5)
            self.set_font("JUNO Solar Lt", "B", 12)
            self.cell(0, 6, "Optionales Zubehör zur Anlagenoptimierung", 0, 0, "L")
            self.set_y(y + 10)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, "Optionales Zubehör beschreibt Hardware, die zur Erfüllung der Grundfunktion einer Photovoltaikanlage nicht benötigt werden. Das optionales Zubehör kann die Effizienz und/oder Funktionsvielfalt ehöhen bzw. erweiter.", 0, 0, "L")  # type: ignore

        y += 25
        if data["hersteller"] == "Huawei":

            if data["anzOptimierer"] > 0:
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
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, str(data["anzOptimierer"]) + " Stk.", 0, "L")
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 20

            # NOTSTROM

            if data["notstrom"]:

                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)

                self.cell(0, 6, "Huawei Backup-Box-B1", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)

                self.multi_cell(
                    0,
                    5,
                    "∙ Einphasige Stromversorgung über Notstromsteckdose\n∙ Produktgarantie: 2 Jahre",
                    0,
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, "1 Stk.", 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 20

            # WANDHALTERUNG

            if data["anzWandhalterungSpeicher"] > 0:

                # Tabelle Eintrag Wandhalterung
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Wandhalterung für Batteriespeicher", 0, 0, "L")
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, str(data["anzWandhalterungSpeicher"]), 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 10

            # Tabelle Eintrag Thor
            if data["thor"] == True:
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
                self.multi_cell(0, 6, "1 Stk.", 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 25

            # ELWA

            if data["elwa"] == True:
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
                self.multi_cell(0, 6, "1 Stk.", 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 15

        if data["hersteller"] == "Viessmann":

            # OPTIMIERER VIESSMANN
            if data["anzOptimierer"] > 0:
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
                    6,
                    "∙ individuelle Schattenerkennung pro Modul\n∙ Produktgarantie: 25 Jahre",
                    0,
                    0,
                    "L",
                )
                self.set_y(y + 5)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, str(data["anzOptimierer"]) + " Stk.", 0, "L")
                self.set_y(y + 5)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")

                y += 20

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
                self.set_y(y + 5)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 5, "1 Stk.", 0, "L")
                self.set_y(y + 5)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")

                y += 15

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
                y += 10

            if data["notstrom"]:
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
                self.multi_cell(0, 6, "1 Stk.", 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 25

            # GRIDBOX

            if data["wallboxAnz"] >= 2:
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Viessmann GridBox 2.0", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)

                self.multi_cell(
                    0,
                    5,
                    "∙ Optionale Anbindung und Visualisierung der Verbrauchswerte\nexterner Geräte (z.B. Warmwasseraufbereitung)\n∙ Produktgarantie: 2 Jahre",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, "1 Stk.", 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 25

            # Tabelle Eintrag Thor
            if data["thor"] == True:

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
                self.multi_cell(0, 6, "1 Stk.", 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")

        return eintrag

    def lastPage(self, data, eintrag):
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
        sum = data["angebotssumme"]
        print(data["angebotssumme"])
        brutto = convertCurrency("{:,.2f} €".format(sum))
        mwst = convertCurrency("{:,.2f} €".format(sum * steuer))
        netto = convertCurrency("{:,.2f} €".format(sum * (1 + steuer)))
        self.multi_cell(0, 6, f'{str(data["kWp"])} kWp\n \n{brutto}\n{mwst}', 0, "R")
        self.set_y(70)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, netto, 0, 0, "R")
        self.line(175, 70, 197, 70)
        # Verbindlichkeiten
        self.set_y(80)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Verbindlichkeiten", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(85)
        self.cell(0, 6, "Das vorliegende Angebot ist gültig bis zum:", 0, 0, "L")
        self.set_x(105)
        self.cell(0, 6, data["gueltig"], 0, 0, "L")
        # Vollmacht
        self.set_y(95)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Vollmacht", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(100)
        self.multi_cell(0, 6, "Zur Realisierung des Projektes, zur Anmeldung der Photovoltaik-Anlage beim Netzbetreiber, zur Registrierung der Photovoltaik-Anlage bei der Bundesnetzagentur, etc. erteilt der Auftraggeber dem Auftragnehmer eine Vollmacht gem. Anlage.", 0, 0, "L")  # type: ignore
        # Garantiebediungen
        self.set_y(120)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Garantiebedingungen", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(125)
        self.multi_cell(0, 6, "Die Garantie der Hardware richtet sich nach den gültigen Garantiebedingungen des jeweiligen Herstellers.", 0, 0, "L")  # type: ignore
        # Auftragserteilung
        self.set_y(135)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Auftragserteilung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(140)
        self.multi_cell(0, 6, "Die oben stehenden Angebotsdetails werden akzeptiert und der Auftrag nach Prüfung der technischen Machbarkeit erteilt. Bis zur vollständigen Zahlung verbleibt das Eigentum an der Photovoltaik-Anlage beim Auftragnehmer. Der Auftraggeber tritt bis dahin die Ansprüche aus der Einspeisevergütung an den Auftragnehmer ab. Des Weiteren gestattet der Auftragnehmer bis zur vollständigen Zahlung dem Auftraggeber, die Photovoltaik-Anlage kostenfrei auf den Dachflächen zu belassen und zu betreiben.", 0, 0, "L")  # type: ignore
        self.set_y(170)
        self.multi_cell(0, 6, "Die Installation der Photovoltaikanlage erfolgt an einem Zählpunkt. Besitzt der Auftraggeber mehrere Stromzähler bzw. Zählpunkte (z.B. für eine Wärmepumpe) und möchte diese zusammenlegen, bietet der Auftragnehmer die Abmeldung verschiedener Zählpunkte beim Netzbetreiber an. Nach dem Ausbau der abgemeldeten Stromzähler durch den Netzbetreiber bleiben die dort installierten Verbraucher stromlos! Das erneute Verdrahten der stromlosen Verbraucher ist kein Bestandteil des hier vorliegenden Auftrags. Der Auftraggeber organisiert eigenständig Fachpersonal, welches die Verdrahtung durchführt.", 0, 0, "L")  # type: ignore
        # Zahlungsmodalitäten
        self.set_y(210)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Zahlungsmodalitäten", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(215)
        if data["zahlungs_bedingungen"]:
            if data["zahlungs_bedingungen"] == "20 – 70 – 10 %":
                self.multi_cell(
                    0,
                    6,
                    "20% bei Auftragsbestätigung\n70% bei Baubeginn\n10% bei Netzanschluss",
                    0,
                    0,
                    "L",
                )  # type: ignore
            elif data["zahlungs_bedingungen"] == "10 – 80 – 10 %":
                self.multi_cell(
                    0,
                    6,
                    "10% bei Auftragsbestätigung\n80% bei Baubeginn\n10% bei Netzanschluss",
                    0,
                    0,
                    "L",
                )  # type: ignore
            elif data["zahlungs_bedingungen"] == "100 – 0 – 0 %":
                self.multi_cell(
                    0,
                    6,
                    "100% bei Auftragsbestätigung\n0% bei Baubeginn\n0% bei Netzanschluss",
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
        self.line(11, 255, 88, 255)
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

    def page5(self, eintrag):
        self.is_last_page = True
        self.add_page()
        self.set_text_color(0)
        self.set_auto_page_break(auto=True, margin=15)

        bold_texts = [
            """Allgemeine Geschäftsbedingungen der JUNO SOLAR Home GmbH & Co. KG über
    die Lieferung, Installation und Inbetriebnahme von Solaranlagen
    § 1 Geltungsbereich, Begriffsbestimmungen""",
            "§ 2 Vertragsschluss",
            "§ 3 Leistungen des Anbieters",
            "§ 4 Leistungsänderungen",
            "§ 5 Pflichten des Kunden",
            "§ 6 Vergütung (Preis) und Zahlungsmodalitäten",
            "§ 7 Herstellergarantien",
            "§ 8 Nachunternehmer",
            "§ 9 Eigentumsvorbehalt",
            "§ 10 Leistungsstörungen",
            "§ 11 Abnahme",
            "§ 12 Haftung",
            "§ 13 Höhere Gewalt",
            "§ 14 Widerrufsbelehrung",
            "Widerrufsbelehrung\nWiderrufsrecht",
            "Folgen des Widerrufs",
            "Muster-Widerrufsformular",
            "§ 15 Online-Streitbeilegung",
            "§ 16 Datenschutz",
            "§ 17 Schlussbestimmungen",
        ]

        regular_texts = [
            """(1) Für die Geschäftsbeziehung zwischen der JUNO SOLAR Home GmbH & Co. KG,
Ziegelstraße 1a, 08412 Werdau (im Folgenden: Anbieter) und dem Kunden gelten
ausschließlich die nachfolgenden Allgemeinen Geschäftsbedingungen in ihrer
zum Zeitpunkt der Bestellung gültigen Fassung. Abweichende Allgemeine
Geschäftsbedingungen des Kunden werden nicht anerkannt, es sei denn, der
Anbieter stimmt ihrer Geltung ausdrücklich schriftlich zu. Dies gilt auch dann,
wenn der Anbieter die Leistung an den Kunden in Kenntnis dessen
Vertragsbedingungen ausführt.
(2) Der Kunde ist Verbraucher, soweit der Zweck der georderten Lieferungen und
Leistungen nicht überwiegend seiner gewerblichen oder selbständigen
beruflichen Tätigkeit zugerechnet werden kann. Dagegen ist Unternehmer jede
natürliche oder juristische Person oder rechtsfähige Personengesellschaft, die
beim Abschluss des Vertrags in Ausübung ihrer gewerblichen oder selbständigen
beruflichen Tätigkeit handelt""",
            """(1) Der Anbieter betreibt unter der Domain https://www.juno-solar.com eine
Internetpräsenz. Die von dem Kunden auf der Internetpräsenz anzugebenden
Daten dienen als Grundlage für die spätere Angebotserstellung durch den
Anbieter. Die auf der Internetpräsenz zum Zwecke einer Angebotserstellung
durch den Anbieter erhobenen Daten sind deshalb wahrheitsgemäß anzugeben.
Bei den auf der Internetpräsenz dargestellten Beispielen handelt es sich nicht um
verbindliche Angebote. Die auf der Internetpräsenz dargestellten Angaben wie
Erträge bzw. Gewinne, die mit dem Betrieb der Solaranlage erzielt werden können,
stellen lediglich Prognosen dar und bilden nicht die tatsächlichen Gegebenheiten
ab.
(2) Aufgrund der auf der Internetpräsenz vom Kunden angegebenen Daten oder,
falls diese nicht ausreichend sind, aufgrund der vom Anbieter vor Ort
aufgenommenen Daten, erhält der Kunde ein Angebot des Anbieters. Anlässlich
des Vor-Ort Termins wird ein technischer Aufnahmebogen erstellt. Das Angebot
wird entweder in Schriftform, per Fax oder elektronisch an den Kunden
übermittelt.
(3)Mit Übermittlung des vom Kunden unterzeichneten Angebots an den Anbieter
in Schriftform, per Fax oder in elektronischer Form schließt der Kunde den
kostenpflichtigen Vertrags über die Lieferung, Installation und Inbetriebnahme
einer Solaranlage ab. Die Bestätigung des Angebots durch den Anbieter erfolgt
durch Übermittlung einer Auftragsbestätigung in Schriftform, per Fax oder in
elektronischer Form.
(4) Der Vertrag wird erst mit Zugang dieser Auftragsbestätigung des Anbieters
beim Kunden wirksam. Die Auftragsbestätigung erfolgt entweder durch
Übermittlung in Schriftform, per Fax oder in elektronischer Form. Geht dem
Kunden die Auftragsbestätigung nicht innerhalb einer Frist von 4 Wochen nach
Zugang des Angebots des Kunden beim Anbieter zu, gilt der Vertrag als nicht
zustande gekommen.
(5) Vertragsbestandteile sind in nachstehender Reihen- und Rangfolge:
(a) die Angaben des Kunden
(b) das Angebot des Anbieters
(c) diese AGB.""",  # regular_text2
            """(1) Der Anbieter verpflichtet sich gegenüber dem Kunden, die ihm angebotene
und bestätigte (siehe § 2 (2)-(5)) Solaranlage zu liefern, zu installieren und in
Betrieb zu nehmen. Hierunter fallen auch die Beratung, Planung, Anmeldung
sowie die Registrierung bei Behörden, soweit sich aus dem Angebot nichts
anderes ergibt.
(2) Der Anbieter behält sich vor, bei Nichtverfügbarkeit einzelner Komponenten
solche mit vergleichbarer Qualität und Ausstattung zu liefern. Teillieferungen sind
zulässig, soweit sie dem Kunden zumutbar sind.""",  # regular_text3
            """Stellt sich nach Vertragsabschluss heraus, dass Abweichungen von den zuvor vom
Kunden gemachten Angaben oder vor Ort feststellbaren tatsächlichen
Gegebenheiten erkennbar werden, die eine Änderung der Solaranlage erfordern,
behält sich der Anbieter vor, die von ihm angebotene Solaranlage unter
Berücksichtigung der berechtigten Interessen des Kunden wie auch des Anbieters
im Rahmen der Zumutbarkeit beider Parteien zu ändern. Sofern und soweit eine
Anpassung der Gegenleistung notwendig wird (günstigerer oder höherer Preis),
wird der Anbieter den Mehr- oder Minderaufwand ermitteln und die Parteien
werden sich über eine entsprechende Vertragsanpassung einigen. Kommt eine
Einigung zwischen den Parteien nicht innerhalb von 14 Tagen ab Kenntnis des
Anbieters von der Abweichung und Mitteilung dieser Erkenntnis gegenüber dem
Kunden nicht zustande, ist der Anbieter berechtigt, von dem Vertrag
zurückzutreten. Gleiches gilt für den Fall, dass eine notwendige Anpassung nicht
möglich oder durchführbar ist.""",  # regular_text4
            """(1) Der Kunde ist zur Mitwirkung verpflichtet, soweit sich das aus den in diesem
Vertrag und in dem Angebot geregelten Pflichten ergibt oder dies sonst zur
Erfüllung dieses Vertrags erforderlich ist oder wird.
(2) Der Kunde ist insbesondere verpflichtet, vor Errichtung der Solaranlage bei der
Einholung der für die Errichtung der Solaranlage erforderlichen Zustimmungen,
Genehmigungen und/oder Mitteilungen mitzuwirken. Gleiches gilt bei
notwendigen Änderungen, Ergänzungen oder bei
Auflagen/Nebenbestimmungen.
(3) Der Kunde wird dem Anbieter den Zählerwechsel durch den Energieversorger
unverzüglich mitteilen, um eine zügige Inbetriebnahme sicherstellen zu können.
(4) Der Kunde ist verpflichtet, die jeweils aktuellen und anwendbaren rechtlichen,
insbesondere baurechtlichen Anforderungen sowie Anforderungen nach dem
jeweils aktuellen Erneuerbare-Energien-Gesetz sowie Technische
Anschlussbedingungen (TAB) zu beachten, welche die Installation der Solaranlage
voraussetzt.
(5) Der Kunde stellt dem Anbieter unentgeltlich zur Verfügung:
(a) Lager- und Arbeitsplätze (für die vom Kunden bestellten Komponenten der
Solaranlage)
(b) Wasseranschluss für die Baustelle
(c) Stromanschluss für die Baustelle.
(6) Der Kunde versichert, dass er Eigentümer des Gebäudes ist, auf dem die
Solaranlage errichtet werden soll oder aber über eine anderweitige Berechtigung
zum Vertragsschluss hinsichtlich der Errichtung der Solaranlage für dieses
Gebäude verfügt und weist dem Anbieter dessen Berechtigung auf Verlangen für
den Anbieter kostenfrei nach.
(7) Soweit zur Errichtung der Solaranlage notwendig, wird der Kunde dem
Anbieter bzw. den vom Anbieter beauftragten Dritten nach Terminabstimmung
ungehinderten Zugang zu den Grundstücken, Gebäuden, Gebäudeteilen bzw.
Dachflächen, auf denen die Solaranlage installiert werden soll, gewähren. Soweit
der Kunde selbst Umbau- und/oder Vorarbeiten durchführt, um eine
vertragsgerechte Errichtung der Solaranlage gewährleisten zu können, müssen
diese Leistungen bis zum vereinbarten Termin zur Errichtung der Solaranlage
fachgerecht abgeschlossen worden sein. Der Lagerplatz für die Paletten muss
mittels Hubwagens ebenerdig zugänglich sein.
(8) Der Kunde ist verpflichtet, die Solaranlage nach deren Errichtung abzunehmen
(näheres hierzu regelt § 11).
(9) Sofern und soweit die angelieferte Ware Transportschäden aufweist, wird der
Kunde dem jeweiligen Mitarbeiter des Transportunternehmens gegenüber diese
sofort reklamieren und den Anbieter hierüber schnellstmöglich unterrichten.
Gewährleistungsrechte des Kunden werden hierdurch nicht berührt.""",  # regular_text5
            """(1) Alle Preisangaben des Anbieters verstehen sich einschließlich der jeweils
gültigen gesetzlichen Umsatzsteuer. Die Umsatzsteuer wird gegebenenfalls
gesondert ausgewiesen.
(2) Die Vergütung ergibt sich aus dem jeweiligen Angebot.
(3) Der verhandelte endgültige Angebotspreis ist ein Pauschalpreis für die
vollständige Ausführung der vereinbarten Leistungen.
(4) Der Kunde erklärt, kein Bauleistender im Sinne des § 13b UStG zu sein.
(5) Die Vergütung wird in folgenden Abschlagszahlungen fällig:
(a) 20 % des Gesamtpreises nach Erhalt der Auftragsbestätigung
(b) 70 % des Gesamtpreises mit Baubeginn (bei Einrichtung der Baustelle
hat der Kunde einen Zahlungsnachweis vorzulegen)
(c) 10 % des Gesamtpreises mit erstmaliger technischer Inbetriebnahme
nach EEG.
(6) Der Anbieter ist berechtigt, sämtliche Ansprüche, Eigentumsrechte und
Anwartschaftsrechte aus diesem Vertragsverhältnis gegenüber dem Kunden an
Dritte abzutreten.""",  # regular_text6
            """Soweit ein Hersteller einzelner, vom Anbieter gelieferter, Komponenten eine
Garantie für diese Produkte gibt, kann sich der Kunde zur Geltendmachung von
Rechten aus diesem Vertragsverhältnis nicht an den Anbieter wenden. Das
Garantieverhältnis besteht ausschließlich zwischen dem Hersteller als
Garantiegeber und dem Kunden. Der Anbieter ist kein Erklärungsempfänger oder
Erklärungsgegner des Garantiegebers. Dies gilt auch für den Fall, dass derartige
Garantien auf der Internetpräsenz des Anbieters oder anderweitig beworben
werden.""",  # regular_text7
            """Der Einsatz von Nachunternehmern ist dem Anbieter grundsätzlich gestattet. Die
vom Anbieter auszuwählenden Nachunternehmer müssen sich gewerbsmäßig
mit der Ausführung der zu vergebenden Leistung befassen. Sie müssen
fachkundig, leistungsfähig und zuverlässig sein.""",  # regular_text8
            """(1) Handelt es sich bei dem Kunden um einen Verbraucher, verbleibt die gelieferte
Ware bis zur vollständigen Bezahlung im Eigentum des Anbieters.
(2) Handelt es sich bei dem Kunden um eine juristische Person des öffentlichen
Rechts, ein öffentlich-rechtl. Sondervermögen oder einen Unternehmer in
Ausübung seiner gewerblichen oder selbstständigen beruflichen Tätigkeit, gilt
folgendes ((3) bis (5)):
(3) Bis zur vollständigen Bezahlung aller gegenwärtigen und künftigen
Forderungen des Anbieters aus dem Werkvertrag und einer laufenden
Geschäftsbeziehung (gesicherte Forderungen) behält sich der Anbieter das
Eigentum an den verkauften Waren vor.
(4) Die unter Eigentumsvorbehalt stehenden Waren dürfen vor vollständiger
Bezahlung der gesicherten Forderungen weder an Dritte verpfändet, noch zur
Sicherheit übereignet werden. Der Kunde hat den Anbieter unverzüglich
schriftlich zu benachrichtigen, wenn ein Antrag auf Eröffnung eines
Insolvenzverfahrens gestellt oder soweit Zugriffe Dritter (z.B. Pfändungen) auf die
dem Anbieter gehörenden Waren erfolgen.
(5) Bei vertragswidrigem Verhalten des Kunden, insbesondere bei Nichtzahlung
der fälligen Vergütung, ist der Anbieter berechtigt, nach den gesetzlichen
Vorschriften vom Vertrag zurückzutreten oder/und die Ware auf Grund des
Eigentumsvorbehalts heraus zu verlangen. Das Herausgabeverlangen beinhaltet
nicht zugleich die Erklärung des Rücktritts; der Anbieter ist vielmehr berechtigt,
lediglich die Ware heraus zu verlangen und sich den Rücktritt vorzubehalten.
Zahlt der Kunde die fällige Vergütung nicht, darf der Anbieter diese Rechte nur
geltend machen, wenn er dem Kunden zuvor erfolglos eine angemessene Frist
zur Zahlung gesetzt hat oder eine derartige Fristsetzung nach den gesetzlichen
Vorschriften entbehrlich ist.""",  # regular_text9
            """Der Anbieter haftet für Leistungsstörungen nach den hierfür geltenden
gesetzlichen Vorschriften (§§ 633 ff. BGB). """,  # regular_text10
            """Der Kunde ist verpflichtet, das vertragsmäßig hergestellte Werk abzunehmen,
sofern nicht nach der Beschaffenheit des Werkes die Abnahme ausgeschlossen
ist. Wegen unwesentlicher Mängel kann die Abnahme nicht verweigert werden. Im
Übrigen gelten § 640a BGB sowie § 650b BGB.""",  # regular_text11
            """(1) Soweit sich aus diesen AGB einschließlich der nachfolgenden Bestimmungen
nichts anderes ergibt, haftet der Anbieter bei einer Verletzung von vertraglichen
und außervertraglichen Pflichten nach den gesetzlichen Vorschriften.
(2) Auf Schadensersatz haftet der Anbieter – gleich aus welchem Rechtsgrund –
im Rahmen der Verschuldenshaftung bei Vorsatz und grober Fahrlässigkeit. Bei
einfacher Fahrlässigkeit haftet der Anbieter vorbehaltlich eines milderen
Haftungsmaßstabs nach gesetzlichen Vorschriften (zB für Sorgfalt in eigenen
Angelegenheiten) nur
a) für Schäden aus der Verletzung des Lebens, des Körpers oder der Gesundheit,
b) für Schäden aus der nicht unerheblichen Verletzung einer wesentlichen
Vertragspflicht (Verpflichtung, deren Erfüllung die ordnungsgemäße
Durchführung des Vertrags überhaupt erst ermöglicht und auf deren Einhaltung
der Vertragspartner regelmäßig vertraut und vertrauen darf); in diesem Fall ist die
Haftung des Anbieters jedoch auf den Ersatz des vorhersehbaren, typischerweise
eintretenden Schadens begrenzt.
(3) Die sich aus (2) ergebenden Haftungsbeschränkungen gelten auch bei
Pflichtverletzungen durch bzw. zugunsten von Personen, deren Verschulden der
Anbieter nach gesetzlichen Vorschriften zu vertreten hat. Sie gelten nicht, soweit
der Anbieter einen Mangel arglistig verschwiegen oder eine Garantie
übernommen hat und für Ansprüche des Kunden nach dem
Produkthaftungsgesetz.
(4) Wegen einer Pflichtverletzung, die nicht in einem Mangel besteht, kann der
Kunde nur zurücktreten oder kündigen, wenn der Anbieter die Pflichtverletzung
zu vertreten hat. Ein freies Kündigungsrecht des Kunden wird ausgeschlossen. Im
Übrigen gelten die gesetzlichen Voraussetzungen und Rechtsfolgen.""",  # regular_text12
            """Der Anbieter haftet nicht für Unmöglichkeit der Lieferung/Leistungserbringung
oder für Lieferverzögerungen, soweit diese durch höhere Gewalt oder sonstige,
zum Zeitpunkt des Vertragsabschlusses nicht vorhersehbare Ereignisse (zB.
Betriebsstörungen aller Art, Schwierigkeiten in der Material- oder
Energiebeschaffung, Transportverzögerungen, Streiks, rechtmäßige
Aussperrungen, Mangel an Arbeitskräften, Energie oder Rohstoffen,
Schwierigkeiten bei der Beschaffung von notwendigen behördlichen
Genehmigungen, behördliche Maßnahmen oder die ausbleibende, nicht richtige
oder nicht rechtzeitige Belieferung durch Lieferanten, Pandemien wie bspw.
COVID) verursacht worden sind, die der Anbieter nicht zu vertreten hat. Sofern
solche Ereignisse die Lieferung oder Leistung des Anbieters wesentlich
erschweren oder unmöglich machen und die Behinderung nicht nur von
vorübergehender Dauer sind, ist der Anbieter zum Rücktritt vom Vertrag
berechtigt. Bei Hindernissen vorübergehender Dauer verlängern sich die Liefer-oder 
Leistungsfristen oder verschieben sich die Liefer- oder Leistungstermine um
den Zeitraum der Behinderung zuzüglich einer angemessenen Anlauffrist. Soweit
dem Kunden infolge der Verzögerung die Abnahme der Lieferung oder Leistung
nicht zuzumuten ist, kann er durch unverzügliche schriftliche Erklärung
gegenüber dem Anbieter vom Vertrag zurücktreten.""",  # regular_text13
            """(1) Verbraucher haben grundsätzlich ein gesetzliches Widerrufsrecht, über das der
Anbieter nach Maßgabe des gesetzlichen Musters nachfolgend informiert. In (2)
findet sich ein Muster-Widerrufsformular. Sie haben das Recht, binnen vierzehn Tagen
ohne Angaben von Gründen diesen Vertrag zu widerrufen.
Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses.
Sie beginnt nicht zu laufen, bevor Sie diese Belehrung in Textform erhalten
haben.
Um Ihr Widerrufsrecht auszuüben, müssen Sie uns (JUNO SOLAR Home GmbH
& Co. KG, Ziegelstraße 1a, 08412 Werdau, Telefon: 03761/4170800, Telefax:
03761/4170849, E-Mail: info@juno-solar.de) mittels einer eindeutigen
Erklärung (z.B. ein mit der Post versandter Brief, Telefax oder E-Mail) über Ihren
Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür das
beigefügte Muster-Widerrufsformular verwenden, das jedoch nicht
vorgeschrieben ist.
Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die
Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.""",  # regular_text14
            """Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir
von Ihnen erhalten haben, einschließlich der Lieferkosten (mit Ausnahme der
zusätzlichen Kosten, die sich daraus ergeben, dass Sie eine andere Art der
Lieferung als die von uns angebotene, günstige Standardlieferung gewählt
haben), unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag
zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrages bei
uns eingegangen ist. Für diese Rückzahlung verwenden wir dasselbe
Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben,
es sei denn, mit Ihnen wurde ausdrücklich etwas anderes vereinbart; in keinem
Fall werden Ihnen wegen dieser Rückzahlung Entgelte berechnet.
Haben Sie verlangt, dass die Vertragsleistung während der Widerrufsfrist
beginnen soll, so haben Sie uns einen angemessenen Betrag zu zahlen, der
dem Anteil der bis zu dem Zeitpunkt, zu dem Sie uns von der Ausübung des
Widerrufsrechts hinsichtlich dieses Vertrags unterrichten, bereits erbrachten
Vertragsleistungen im Vergleich zum Gesamtumfang der im Vertrag
vorgesehenen Leistungen entspricht.
(2) Über das Muster-Widerrufsformular informiert der Anbieter nach der
gesetzlichen Regelung wie folgt:""",  # regular_text15
            """(Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular
aus und senden Sie es zurück.)
— An JUNO SOLAR Home GmbH & Co. KG, Ziegelstraße 1a, 08412 Werdau,
Telefon: 03761/4170800, Telefax: 03761/4170849, E-Mail: info@juno-solar.de:
            -   Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*)
                abgeschlossenen Vertrag über den Kauf der folgenden
                Waren (*)/ die Erbringung der folgenden Dienstleistung (*)
            -   Bestellt am
            -   Angebotsnummer
            -   Name des/der Verbraucher(s)
            -   Anschrift des/der Verbraucher(s)
            -   Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf
                Papier)
            -   Datum""",  # regular_text16
            """(1) Die europäische Kommission stellt eine Plattform zur online-Streitbeilegung
bereit, die im Internet unter https://ec.europa.eu/consumers/odr/ zu finden ist.
(2) Der Anbieter ist nicht verpflichtet, an einem Streitbeilegungsverfahren vor
einer Verbraucher-schlichtungsstelle teilzunehmen und nimmt auch nicht
freiwillig daran teil.""",  # regular_text17
            """Die an den Anbieter übermittelten Daten werden in Übereinstimmung mit dem
BDSG und der DSGVO gespeichert und verarbeitet. Die einzelnen Rechte und
Pflichten ergeben sich aus der Datenschutzerklärung. Diese finden Sie unter
https://www.juno-solar.com.""",  # regular_text18
            """(1) Auf Verträge zwischen dem Anbieter und dem Kunden findet das Recht der
Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts Anwendung.
Die gesetzlichen Vorschriften zur Beschränkung der Rechtswahl und zur
Anwendbarkeit zwingender Vorschriften insbes. des Staates, in dem der Kunde als
Verbraucher seinen gewöhnlichen Aufenthalt hat, bleiben unberührt.
(2) Sofern es sich beim Kunden um einen Kaufmann, eine juristische Person des
öffentlichen Rechts oder um ein öffentlich-rechtliches Sondervermögen handelt,
ist Gerichtsstand für alle Streitigkeiten aus Vertragsverhältnissen zwischen dem
Kunden und dem Anbieter der Sitz des Anbieters. Erfüllungsort ist der Sitz des
Anbieters.
(3) Der Vertrag bleibt auch bei rechtlicher Unwirksamkeit einzelner Punkte in
seinen übrigen Teilen verbindlich. Anstelle der unwirksamen Punkte treten, soweit
vorhanden, die gesetzlichen Vorschriften. Soweit dies für eine Vertragspartei eine
unzumutbare Härte darstellen würde, wird der Vertrag jedoch im Ganzen
unwirksam.""",  # regular_text19
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

    def page6(self, certifikate, eintrag):
        self.is_last_page = True
        if certifikate:
            self.add_page()
            self.image(
                certifikate.path,
                x=5,
                y=10,
                w=198,
            )
        else:
            pass


def replace_spaces_with_underscores(s: str) -> str:
    return s.replace(" ", "_")


def createOfferPdf(data, vertrieb_angebot, certifikate, user):
    global title, pages
    title1 = f"{vertrieb_angebot.angebot_id}"

    pages = "7"
    pdf = PDF(title1)
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")

    # create the offer-PDF
    eintrag = 0
    eintrag = pdf.page1(data, eintrag)
    eintrag = pdf.page2(data, eintrag)
    eintrag = pdf.page3(data, eintrag)
    eintrag = pdf.page4(data, eintrag)
    # eintrag = pdf.page4_durchgestrichen(data, eintrag)

    pdf.lastPage(data, eintrag)
    pdf.page6(certifikate, eintrag)
    pdf.page5(eintrag)

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content
