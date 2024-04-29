from math import ceil
from datetime import datetime, date
from fpdf import FPDF
from config import settings
from vertrieb_interface.pdf_services.helper_functions import convertCurrency
import os

title = ""
pages = "4"


class PDF(FPDF):
    def header(self):
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarLt.ttf")
        self.add_font("JUNO Solar Lt", "", font_path, uni=True)
        font_path = os.path.join(settings.STATIC_ROOT, "fonts/JUNOSolarRg.ttf")
        self.add_font("JUNO Solar Lt", "B", font_path, uni=True)

        # Position at 1.5 cm from bottom
        self.set_y(15)
        self.set_font("JUNO Solar Lt", "", 12)
        self.set_text_color(0)
        # Page number
        self.cell(0, 10, f"Seite {str(self.page_no())}/{pages}", 0, 0, "")
        self.set_x(40)
        if self.page_no() != 1:
            self.cell(0, 10, title, 0, 0, "")
        self.image(
            os.path.join(settings.MEDIA_ROOT, "fonts/junosolar_logo.jpg"),
            x=170,
            y=10,
            w=30,
            h=15,
        )
        self.ln(15)

    def footer(self):
        self.set_font("JUNO Solar Lt", "", 8)
        self.set_text_color(128)
        self.set_y(-30)
        self.multi_cell(0, 5, "Geschäftsführer: Denny Schädlich\npersönlich haftender Gesellschaftler: Juno Solar Home Verwaltungs GmbH\nSitz Werdau ∙ Amtsgericht Chemnitz HRB 34192 ∙ Steuernummer 227/156/19508 ∙ Ust-IdNr DE 34514953", 0, 0, "L")  # type: ignore
        self.set_y(-30)
        self.set_x(150)
        self.multi_cell(
            0,
            5,
            "Commerzbank Chemnitz\nIBAN DE94 8704 0000 0770 0909 00\nBIC/Swift-Code: COBADEFFXXX",
            0,
            "R",
        )

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
        self.multi_cell(0, 5, f'{data["firma"]}\n{data["kunde"]}\n{data["adresse"]}', 0, 0, "L")  # type: ignore
        self.set_x(130)
        self.set_y(33)
        self.multi_cell(
            0,
            5,
            "JUNO SOLAR Home GmbH & Co. KG\nZiegelstraße 1a\nD-08412 Werdau",
            0,
            "R",
        )
        self.set_x(130)
        self.set_y(53)
        self.multi_cell(0, 5, f'{data["vertriebler"]}\n\nwww.juno-solar.com', 0, "R")
        self.set_y(80)
        self.set_font("JUNO Solar Lt", "B", 17)
        self.cell(0, 6, title, 0, 0, "R")
        # Überschrift und Text
        self.set_font("JUNO Solar Lt", "B", 17)
        self.set_x(0)
        self.set_y(80)
        self.cell(0, 6, "ANGEBOT", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_x(0)
        self.set_y(90)
        self.cell(0, 5, f'Werdau, {date.today().strftime("%d.%m.%Y")}', 0, 0, "L")
        self.set_x(0)
        self.set_y(100)
        self.multi_cell(0, 5, "Gesamtleistung der Anlage:\nStandort der Anlage:", 0, "")
        self.set_y(100)
        self.set_x(70)
        self.multi_cell(0, 5, f'{str(data["kWp"])} kWp\n{data["standort"]}', 0, "L")
        self.set_y(115)
        if "und" in data["anrede"]:
            self.cell(0, 6, f'{data["anrede"]},', 0, 0, "L")
        else:
            self.cell(0, 6, f'{data["anrede"]} {data["kunde"]},', 0, 0, "L")
        self.set_x(0)
        self.set_y(125)
        self.multi_cell(
            0,
            5,
            "vielen Dank für Ihre Anfrage. Wir bieten Ihnen hiermit die komplette Lieferung und Montage folgender Photovoltaikanlage an:",
            0,
            "",
        )
        # Tabelle Beginn
        self.set_font("JUNO Solar Lt", "B", 12)
        self.set_x(0)
        self.set_y(135)
        self.cell(0, 6, "Pos.", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Bezeichnung", 0, 0, "L")
        self.set_x(150)
        self.cell(0, 6, "Menge", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "Gesamtpreis", 0, 0, "R")
        # Gleichstromseitige Installation
        self.line(10, 141, 200, 141)
        self.set_y(144)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Gleichstromseitige Installation", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(145)
        self.multi_cell(
            0,
            5,
            "\nDie gleichstromseitige Installation beschreibt sämtliche Bauteile sowie Dienstleistungen, die sich im Gleichstromkreis befinden. Die Installation des Netzeinspeisegerätes (Wechselrichter) stellt hierbei den Schnittpunkt zur wechselstromseitigen Installation dar.",
            0,
            "L",
        )
        # Tabelle Eintrag 1
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(170)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, data["module"], 0, 0, "L")
        self.set_y(175)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            f'∙ Leistung pro Modul: {data["wpModule"]} Wp\n∙ Produktgarantie: {data["produktGarantie"]}\n∙ Leistungsgarantie: {data["leistungsGarantie"]}',
            0,
            "L",
        )
        self.set_y(170)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, f'{str(data["anzModule"])} Stk', 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, f'{str(data["solarModulePreis"])} €', 0, 0, "R")
        # Tabelle Eintrag 2
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(200)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(
            0, 5, "Wechselrichter Huawei SUN2000 Modell nach Auslegung", 0, 0, "L"
        )
        self.set_y(205)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "∙ inkl. Smart Dongle Wlan + Ethernet\n∙ inkl. Überspannungsschutz AC/DC - Schutzart\n  Typ 2 gemäß EN/IEC 61643-11\n∙ Produktgarantie: "
            + data["garantieJahre"],
            0,
            "L",
        )
        self.set_y(200)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        # Tabelle Eintrag 3
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(230)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, "Solarleitung", 0, 0, "L")
        self.set_y(235)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Solarkabel 2-fach isoliert, UV-beständig, Leitungsverlust DC unter 1%",
            0,
            "L",
        )
        self.set_y(230)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        # Tabelle Eintrag 4
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(245)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.multi_cell(0, 5, "Stecker und Buchsen", 0, "L")
        self.set_y(245)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        # # Tabelle Eintrag 5
        # self.set_font('JUNO Solar Lt', '', 11)
        # self.set_y(255)
        # eintrag += 1
        # self.cell(0, 6, str(eintrag) + ".", 0, 0, 'L')
        # self.set_x(25)
        # self.cell(0, 5, "Unterkonstruktion", 0, 0, 'L')
        # self.set_y(260)
        # self.set_x(25)
        # self.set_font('JUNO Solar Lt', '', 10)
        # self.multi_cell(0, 5, "S-FLEX LEICHTmount rail oder gleichwertig", 0, 'L')
        # self.set_y(255)
        # self.set_x(150)
        # self.set_font('JUNO Solar Lt', '', 11)
        # self.cell(0, 6, "nach Auslegung", 0, 0, 'L')
        # self.set_x(170)
        # self.cell(0, 6, "inklusive", 0, 0, 'R')
        return eintrag

    def page2(self, data, eintrag):
        self.add_page()
        y = 35
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
        self.multi_cell(0, 5, "S-FLEX LEICHTmount rail oder gleichwertig", 0, "L")
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
        self.cell(0, 6, "Potentialausgleich", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Der Potentialausgleich ist in DIN VDE 0100, Teil 540 festgelegt.\nEr dient der Erdung der PV-Anlage und erfolgt nach\nDIN EN 50083-1 (VDE 0855-1).",
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
        # Tabelle Eintrag 7
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
            "Gleichstrom-Elektroinstallation: Montage und Verlegung der Modul-\nUnterkonstruktion sowie Solarmodule bis zu den Wechselrichtern.",
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
        # Tabelle Eintrag 8
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Gerüst", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(0, 5, "Gerüst zur Absturzsicherung.", 0, "L")
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "nach Auslegung", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 15
        # Tabelle Eintrag 9
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Frachtkosten", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0, 5, "Die Frachtkosten beziehen sich auf die Gesamtmaterialien.", 0, "L"
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 15
        # Tabelle Eintrag 10
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
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 20
        # Tabelle Eintrag 11
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Planung", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(0, 5, "komplette Anlagenplanung inkl. Dokumentation.", 0, "L")
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 20
        # Wechselstromseitige Installation und Inbetriebnahme
        self.line(10, y - 4, 200, y - 4)
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
            "\nDie wechselstromseitige Installation beschreibt sämtliche Bauteile sowie Dienstleistungen, die sich im Wechselstromkreis befinden. Die Installation des Wechselrichters stellt hierbei den Schnittpunkt zur gleichstromseitigen Installation dar. Kundenseitig stellt der Zählerschrank bzw. die Übergabestation die Schnittstelle zum Energieversorger dar.",
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
        self.multi_cell(
            0, 5, "Installation und Parametrierung des Wechselrichters", 0, "L"
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        y += 10
        # Tabelle Eintrag 13
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "AC-Installation", 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(0, 5, "mit 5x6mm2 Kupferleitung", 0, "L")
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
        # Tabelle Eintrag 15
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(
            0, 6, "Zählerwechsel (Falls Zweirichtungszähler nicht vorhanden)", 0, 0, "L"
        )
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Der Einbau des Zweirichtungszähler erfolgt durch\nden zuständigen Messstellenbetreiber",
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
        # Tabelle Eintrag 16
        # self.set_font('JUNO Solar Lt', '', 11)
        # self.set_y(y)
        # eintrag += 1
        # self.cell(0, 6, str(eintrag) + ".", 0, 0, 'L')
        # self.set_x(25)
        # self.cell(0, 6, "Programmierung Sicherheitsmanagement (Wirkleistungsbegrenzung)", 0, 0, 'L')
        # self.set_y(240)
        # self.set_x(25)
        # self.set_font('JUNO Solar Lt', '', 10)
        # self.multi_cell(0, 5, "Zur Gewähleistung der Stromnetzstabilität ist im Erneuerbare-Energien-Gesetz (EEG)\nverankert, dass PV-Anlagen ohne eine fernbedienbare Funkrundsteuerung\nihre Maximalleistung auf 70% begrenzen. Anderweitig wird die Vorraussetzung\nzum Beziehen der Einspeisevergütung nicht erfüllt.", 0, 'L')
        # self.set_y(235)
        # self.set_x(150)
        # self.set_font('JUNO Solar Lt', '', 11)
        # self.cell(0, 6, "1", 0, 0, 'L')
        # self.set_x(170)
        # self.cell(0, 6, "inklusive", 0, 0, 'R')

        return eintrag

    def page3(self, data, eintrag):
        self.add_page()
        # Anlagenüberwachung und Visualisierung
        self.set_y(34)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Anlagenüberwachung und Visualisierung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(35)
        self.multi_cell(
            0,
            5,
            "\nDiese Position beschreibt die technischen Bauteile und deren Installation, um eine Anlagenüberwachung und die Visualisierung der Ertragsdaten zu realisieren bzw. darzustellen.",
            0,
            "L",
        )
        # Tabelle Eintrag 17
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(55)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Integriertes Monitoring zur Anlagenüberwachung", 0, 0, "L")
        self.set_y(60)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "mittels Huawei FusionSolar App\nkompatibel mit Android und iOS",
            0,
            "L",
        )
        self.set_y(55)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        # Netzanschlussmanagement
        self.line(10, 76, 200, 76)
        self.set_y(79)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Netzanschlussmanagement", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(80)
        self.multi_cell(
            0,
            5,
            "\nDas Netzanschlussmanagement bearbeitet alle Formulare, die vom Anlagenbetreiber zum Erzielen einer Einspeisevergütung ausgefüllt werden müssen, von der Netzanfrage bis hin zur Anmeldung der PV-Anlage beim EVU, unter Berücksichtigung öffentlicher- und privatrechtlicher Vorschriften.",
            0,
            "L",
        )
        # Tabelle Eintrag 18
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(105)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Anmeldung zum Netzanschluss", 0, 0, "L")
        self.set_y(110)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Mit der Anmeldung zum Netzanschluss wird dem örtlichen Netzbetreiber das\nNetzanschlussbegehren des Anlagenbetreibers übermittelt.",
            0,
            "L",
        )
        self.set_y(105)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        # Tabelle Eintrag 19
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(125)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "EEG-Fertigmeldung und -Inbetriebnahme", 0, 0, "L")
        self.set_y(130)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0, 5, "Die Fertigmeldung erfolgt nach erfolgreichem Bauabschluss.", 0, "L"
        )
        self.set_y(125)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        # Tabelle Eintrag 20
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(140)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Registrierung im Marktstammdatenregister", 0, 0, "L")
        self.set_y(145)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            "Die Registrierung im Marktstammdatenregister ist verpflichtend und muss\nspätestens vier Wochen nach der EEG-Fertigmeldung erfolgen.",
            0,
            "L",
        )
        self.set_y(140)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, "1", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "inklusive", 0, 0, "R")
        return eintrag

    # not in use
    def page4_verschwinden(self, data, eintrag):
        y = 165
        if data["batterieVorh"]:
            # Batteriespeichersystem
            self.line(10, y, 200, y)
            self.set_y(y + 5)
            self.set_font("JUNO Solar Lt", "B", 12)
            self.cell(0, 6, "Batteriespeichersystem", 0, 0, "L")
            self.set_y(y + 10)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, "Ein Batteriespeicher kann überschüssig gewonnene Energie der Photovoltaikanlage zwischenspeichern und abgeben wenn die Leistung der Photovoltaikanlage nicht aussreichend ist.", 0, 0, "L")  # type: ignore
            # Tabelle Eintrag 2X
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y + 25)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Smart Power Sensor", 0, 0, "L")
            self.set_y(y + 30)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(0, 5, "DTSU666-H 250A/50mA", 0, "L")
            self.set_y(y + 25)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.cell(0, 6, "1", 0, 0, "L")
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")
            # Tabelle Eintrag 2X
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y + 40)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Batteriespeicher Huawei LUNA 2000", 0, 0, "L")
            self.set_y(y + 45)
            self.set_x(25)
            # self.set_font('JUNO Solar Lt', '', 10)
            self.multi_cell(0, 5, "Leistungsmodule\nBatteriemodule (je 5 kWh)", 0, "L")
            self.set_y(y + 45)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 5, str(ceil(data["batterieAnz"] / 3)) + "\n" + str(data["batterieAnz"]), 0, 0, "L")  # type: ignore
            self.set_y(y + 40)
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")
            # Seite voll
            y = y + 70
            self.set_y(y)
        if data["optionVorh"]:
            # Optionales Zubehör zur Anlagenoptimierung
            if y == 235 or y == 220:
                self.add_page()
                y = 30
            else:
                self.line(10, y, 200, y)
            self.set_y(y + 5)
            self.set_font("JUNO Solar Lt", "B", 12)
            self.cell(0, 6, "Optionales Zubehör zur Anlagenoptimierung", 0, 0, "L")
            self.set_y(y + 10)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, "Optionales Zubehör beschreibt Hardware, die zur Erfüllung der Grundfunktion einer Photovoltaikanlage nicht benötigt werden. Das optionales Zubehör kann die Effizienz und/oder Funktionsvielfalt ehöhen bzw. erweitern.", 0, 0, "L")  # type: ignore
            if y != 230:
                y += 25
            if data["eddi"] > 0:
                # Tabelle Eintrag Eddi
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "myenergi Leistungsverteiler eddi", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0, 5, "zur Nutzung überschüssiger Energie im Hausnetz", 0, "L"
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, str(data["eddi"]), 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 15
            if data["anzOptimierer"] > 0:
                # Tabelle Eintrag Optimierer
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Modul-Leistungsoptimierer", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(0, 5, "indiviuelle Schattenerkennung pro Modul", 0, "L")
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, str(data["anzOptimierer"]), 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 15
            if data["notstrom"]:
                # Tabelle Eintrag Ersatzstrom
                self.set_font("JUNO Solar Lt", "", 11)
                self.set_y(y)
                eintrag += 1
                self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
                self.set_x(25)
                self.cell(0, 6, "Huawei Ersatzstromversorgung", 0, 0, "L")
                self.set_y(y + 5)
                self.set_x(25)
                self.set_font("JUNO Solar Lt", "", 10)
                self.multi_cell(
                    0,
                    5,
                    "Huawei Backup-Box-B1 zur einphasigen Ersatzstromversorgung",
                    0,
                    "L",
                )
                self.set_y(y)
                self.set_x(150)
                self.set_font("JUNO Solar Lt", "", 11)
                self.multi_cell(0, 6, "1", 0, 0, "L")  # type: ignore
                self.set_y(y)
                self.set_x(170)
                self.cell(0, 6, "inklusive", 0, 0, "R")
                y += 15
        if data["wallboxVorh"]:
            # Ladestation für E-Fahrzeug (Wallbox)
            if y == 235 or y == 220:
                self.add_page()
                y = 30
            else:
                self.line(10, y, 200, y)
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
            self.cell(0, 6, "Ladestation für E-Fahrzeug (Wallbox)", 0, 0, "L")
            self.set_y(y + 30)
            self.set_x(25)
            # self.set_font('JUNO Solar Lt', '', 10)
            self.multi_cell(0, 5, data["wallboxText"], 0, "L")
            self.set_y(y + 30)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 5, data["wallboxAnz"], 0, "L")
            self.set_y(y + 25)
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")
            # Seite voll
            y = y + 55
            self.set_y(y)

    def page4_durchgestrichen(self, data, eintrag):
        y = 160
        # Batteriespeichersystem
        self.line(10, y, 200, y)
        self.set_y(y + 4)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Batteriespeichersystem", 0, 0, "L")
        self.set_y(y + 10)
        self.set_font("JUNO Solar Lt", "", 11)
        self.multi_cell(
            0,
            6,
            "Ein Batteriespeicher kann überschüssig gewonnene Energie der Photovoltaikanlage zwischenspeichern und abgeben, wenn die Leistung der Photovoltaikanlage nicht aussreichend ist.",
            0,
            0,  # type: ignore
            "L",  # type: ignore
        )

        if not data["batterieVorh"]:
            self.line(10, y + 7, 51, y + 7)
            # self.line(10, y + 13, 200, y + 13)
            # self.line(10, y + 19, 92, y + 19)
            # self.line(10, y + 28, 200, y + 28)
            # self.line(25, y + 32.5, 60, y + 32.5)
            # self.line(10, y + 43, 200, y + 43)
            # self.line(25, y + 47.5, 155, y + 47.5)
            # self.line(25, y + 52, 155, y + 52)
        else:
            # Tabelle Eintrag 2X
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y + 25)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Smart Power Sensor", 0, 0, "L")
            self.set_y(y + 30)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(0, 5, "DTSU666-H 250A/50mA", 0, "L")
            self.set_y(y + 25)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.cell(0, 6, "1", 0, 0, "L")
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")
            # Tabelle Eintrag 2X
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y + 40)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Batteriespeicher Huawei LUNA 2000", 0, 0, "L")
            self.set_y(y + 45)
            self.set_x(25)
            # self.set_font('JUNO Solar Lt', '', 10)
            self.multi_cell(0, 5, "Leistungsmodule\nBatteriemodule (je 5 kWh)", 0, "L")
            self.set_y(y + 40)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, str(ceil(data["batterieAnz"] / 3)) + "\n" + str(data["batterieAnz"]), 0, 0, "L")  # type: ignore
            self.set_y(y + 40)
            self.set_x(170)
            self.cell(0, 6, "inklusive", 0, 0, "R")

        # Seite voll
        y = y + 60
        self.set_y(y)
        if data["anzWandhalterungSpeicher"] > 0:
            # self.line(10, y + 3, 200, y + 3)
            # self.line(25, y + 7.5, 83, y + 7.5)
            # Tabelle Eintrag Optimierer
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Wandhalterung für Batteriespeicher", 0, 0, "L")
            self.set_y(y + 0)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, str(data["anzWandhalterungSpeicher"]), 0, 0, "L")  # type: ignore
            self.set_y(y)
            self.set_x(170)
            self.cell(0, 6, str(data["wandhalterungSpeicherPreis"]), 0, 0, "R")
            y += 15
        else:
            y += 15
        # Optionales Zubehör zur Anlagenoptimierung
        self.add_page()
        y = 30
        y_tmp = 0
        if not data["optionVorh"]:
            self.line(10, y + 7, 86, y + 7)
            # self.line(10, y + 13, 200, y + 13)
            # self.line(10, y + 19, 148, y + 19)
        self.set_y(y + 4)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Optionales Zubehör zur Anlagenoptimierung", 0, 0, "L")
        self.set_y(y + 10)
        self.set_font("JUNO Solar Lt", "", 11)
        self.multi_cell(0, 6, "Optionales Zubehör beschreibt Hardware, die zur Erfüllung der Grundfunktion einer Photovoltaikanlage nicht benötigt werden. Das optionales Zubehör kann die Effizienz und/oder Funktionsvielfalt erhöhen bzw. erweitern.", 0, 0, "L")  # type: ignore
        y += 25
        if data["eddi"] > 0:
            # self.line(10, y + 3, 200, y + 3)
            # self.line(25, y + 7.5, 93, y + 7.5)
            # Tabelle Eintrag Eddi
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "myenergi Leistungsverteiler eddi", 0, 0, "L")
            self.set_y(y + 5)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(
                0, 5, "zur Nutzung überschüssiger Energie im Hausnetz", 0, "L"
            )
            self.set_y(y)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, "1", 0, 0, "L")  # type: ignore
            self.set_y(y)
            self.set_x(170)
            self.cell(0, 6, f'{str(data["eddiPreis"])} €', 0, 0, "R")
            y += 15
        else:
            y_tmp += 15
        if data["anzOptimierer"] > 0:
            # self.line(10, y + 3, 200, y + 3)
            # self.line(25, y + 7.5, 83, y + 7.5)
            # Tabelle Eintrag Optimierer
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Modul-Leistungsoptimierer", 0, 0, "L")
            self.set_y(y + 5)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(0, 5, "indiviuelle Schattenerkennung pro Modul", 0, "L")
            self.set_y(y)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, str(data["anzOptimierer"]), 0, 0, "L")  # type: ignore
            self.set_y(y)
            self.set_x(170)
            self.cell(0, 6, f'{str(data["gesamtOptimizerPreis"])} €', 0, 0, "R")
            y += 15
        else:
            y_tmp += 15
        if data["notstrom"]:
            # self.line(10, y + 3, 200, y + 3)
            # self.line(25, y + 7.5, 109, y + 7.5)
            # Tabelle Eintrag Ersatzstrom
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Huawei Ersatzstromversorgung", 0, 0, "L")
            self.set_y(y + 5)
            self.set_x(25)
            self.set_font("JUNO Solar Lt", "", 10)
            self.multi_cell(
                0,
                5,
                "Huawei Backup-Box-B1 zur einphasigen Ersatzstromversorgung",
                0,
                "L",
            )
            self.set_y(y)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, "1", 0, 0, "L")  # type: ignore
            self.set_y(y)
            self.set_x(170)
            self.cell(0, 6, f'{str(data["notstromPreis"])} €', 0, 0, "R")
        y += 15
        y += y_tmp
        # Ladestation für E-Fahrzeug (Wallbox)
        self.line(10, y, 200, y)
        self.set_y(y + 4)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Ladestation für E-Fahrzeug (Wallbox)", 0, 0, "L")
        self.set_y(y + 10)
        self.set_font("JUNO Solar Lt", "", 11)
        self.multi_cell(0, 6, "Mit einer Wallbox können Sie die Energie Ihrer Photovoltaikanlage zum Laden Ihres Elektrofahrzeugs nutzen. Eine intelligente Steuerung (opt. Zubehör) kann den Ladestrom kontinuierlich der aktuellen Energieerzeugung anpassen.", 0, 0, "L")  # type: ignore
        # self.set_font('JUNO Solar Lt', '', 10)
        if not data["wallboxVorh"]:
            self.line(10, y + 7, 73, y + 7)
            # self.line(10, y + 13, 200, y + 13)
            # self.line(10, y + 19, 165, y + 19)
            # self.line(10, y + 28, 200, y + 28)
        else:
            # Tabelle Eintrag 2X
            self.set_font("JUNO Solar Lt", "", 11)
            self.set_y(y + 30)
            eintrag += 1
            self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            self.set_x(25)
            self.cell(0, 6, "Ladestation für E-Fahrzeug (Wallbox)", 0, 0, "L")
            self.set_y(y + 30)
            self.set_x(25)
            self.multi_cell(0, 6, data["wallboxTyp"], 0, "L")
            self.set_y(y + 30)
            self.set_x(150)
            self.set_font("JUNO Solar Lt", "", 11)
            self.multi_cell(0, 6, str(data["wallboxAnz"]), 0, "L")
            self.set_y(y + 30)
            self.set_x(170)
            self.cell(0, 6, f'{str(data["wallboxPreis"])} €', 0, 0, "R")
        # Seite voll
        y = y + 55
        self.set_y(y)

    def lastPage(self, data):
        self.add_page()
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
        brutto = convertCurrency("{:,.2f} €".format(sum))
        mwst = convertCurrency("{:,.2f} €".format(sum * steuer))
        netto = convertCurrency("{:,.2f} €".format(sum * (1 + steuer)))
        self.multi_cell(0, 6, f'{str(data["kWp"])} kWp\n \n{brutto}\n{mwst}', 0, "R")
        self.set_y(70)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, netto, 0, 0, "R")
        self.line(175, 70, 200, 70)
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
        self.set_y(115)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Garantiebedingungen", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(120)
        self.multi_cell(0, 6, "Die Garantie der Hardware richtet sich nach den gültigen Garantiebedingungen des jeweiligen Herstellers.", 0, 0, "L")  # type: ignore
        # Auftragserteilung
        self.set_y(130)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Auftragserteilung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(135)
        self.multi_cell(0, 6, "Die oben stehenden Angebotsdetails werden akzeptiert und der Auftrag nach Prüfung der technischen Machbarkeit erteilt. Bis zur vollständigen Zahlung verbleibt das Eigentum an der Photovoltaik-Anlage beim Auftragnehmer. Der Auftraggeber tritt bis dahin die Ansprüche aus der Einspeisevergütung an den Auftragnehmer ab. Des Weiteren gestattet der Auftragnehmer bis zur vollständigen Zahlung dem Auftraggeber, die Photovoltaik-Anlage kostenfrei auf den Dachflächen zu belassen und zu betreiben.", 0, 0, "L")  # type: ignore
        self.set_y(165)
        self.multi_cell(0, 6, "Die Installation der Photovoltaikanlage erfolgt an einem Zählpunkt. Besitzt der Auftraggeber mehrere Stromzähler bzw. Zählpunkte (z.B. für eine Wärmepumpe) und möchte diese zusammenlegen, bietet der Auftragnehmer die Abmeldung verschiedener Zählpunkte beim Netzbetreiber an. Nach dem Ausbau der abgemeldeten Stromzähler durch den Netzbetreiber bleiben die dort installierten Verbraucher stromlos! Das erneute Verdrahten der stromlosen Verbraucher ist kein Bestandteil des hier vorliegenden Auftrags. Der Auftraggeber organisiert eigenständig Fachpersonal, welches die Verdrahtung durchführt.", 0, 0, "L")  # type: ignore
        # Zahlungsmodalitäten
        self.set_y(200)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Zahlungsmodalitäten", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(205)
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


def createOfferPdf(data, vertrieb_angebot, user):
    global title, pages
    title = f"{vertrieb_angebot.angebot_id}"
    pages = "5"
    pdf = PDF()
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")

    # create the offer-PDF
    eintrag = 0
    eintrag = pdf.page1(data, eintrag)
    eintrag = pdf.page2(data, eintrag)
    eintrag = pdf.page3(data, eintrag)
    pdf.page4_durchgestrichen(data, eintrag)
    pdf.lastPage(data)

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content
