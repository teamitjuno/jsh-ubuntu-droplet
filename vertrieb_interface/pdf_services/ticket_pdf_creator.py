from config import settings
from math import ceil
from datetime import datetime, date
from vertrieb_interface.pdf_services.helper_functions import convertCurrency
from fpdf import FPDF
import os


title = ""
pages = "2"


class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super(PDF, self).__init__(*args, **kwargs)
        self.is_last_page = False

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
        self.image(
            os.path.join(settings.MEDIA_ROOT, "fonts/junosolar_logo.jpg"),
            x=170,
            y=10,
            w=30,
            h=15,
        )
        # Line break
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
        self.set_fill_color(240)
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
        # self.line(10,65,80,65) #unter Adresse
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
        # Überschrift und Text
        y = 105
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
        self.line(10, 141, 200, 141)
        eintrag = 0
        y = 145

        # Tabelle Eintrag 1
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 5, data["module"], 0, 0, "L")
        self.set_y(y + 5)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        self.multi_cell(
            0,
            5,
            f'∙ Leistung pro Modul: {data["wpModule"]} Wp\n∙ Produktgarantie: {data["produktGarantie"]}\n∙ Leistungsgarantie: {data["leistungsGarantie"]}',
            0,
            "L",
        )
        self.set_y(y)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 6, f'{str(data["modulTicket"])} Stk', 0, 0, "L")
        self.set_x(170)
        self.cell(
            0,
            6,
            convertCurrency("{:,.2f} €".format(data["modulTicketpreis"])),
            0,
            0,
            "R",
        )

        y += 21
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
            # if
            #     self.set_y(y + 5)
            #     self.set_font("JUNO Solar Lt", "B", 12)
            #     self.cell(0, 6, "Ladestation für E-Fahrzeug (Wallbox)", 0, 0, "L")
            #     self.set_y(y + 10)
            #     self.set_font("JUNO Solar Lt", "", 11)
            #     self.multi_cell(0, 6, "Mit einer Wallbox können Sie die Energie Ihrer Photovoltaikanlage zum Laden Ihres Elektrofahrzeugs nutzen. Eine intelligente Steuerung (opt. Zubehör) kann den Ladestrom kontinuierlich der aktuellen Energieerzeugung anpassen.", 0, 0, "L")  # type: ignore
            #     # Tabelle Eintrag 2X
            #     self.set_font("JUNO Solar Lt", "", 11)
            #     self.set_y(y + 25)
            #     eintrag += 1
            #     self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
            #     self.set_x(25)
            #     self.cell(0, 6, "Huawei Fusion Charge AC", 0, 0, "L")
            #     self.set_y(y + 30)
            #     self.set_x(25)
            #     self.set_font("JUNO Solar Lt", "", 10)
            #     self.multi_cell(0, 6, "∙ inkl. Lade- und Lastmanagement\n∙ maximale Ladeleistung: 22 kW\n∙ Parametrierbar auf 11 kW (für KfW Förderung)\n∙ Produktgarantie: 3 Jahre", 0, 0, "L")
            #     self.set_y(y + 25)
            #     self.set_x(25)
            #     # self.set_font('JUNO Solar Lt', '', 10)
            #     self.multi_cell(0, 5, data["wallboxText"], 0, "L")
            #     self.set_y(y + 25)
            #     self.set_x(150)
            #     self.set_font("JUNO Solar Lt", "", 11)
            #     self.multi_cell(0, 5, str(data["wallboxAnz"]), 0, "L")
            #     self.set_y(y + 25)
            #     self.set_x(170)
            #     self.cell(0, 6, "inklusive", 0, 0, "R")

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

                y += 17
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
            "Leistung bisher \nLeistungsgewinn \nGesamtleistung\n \nNetto\nMwSt. "
            + str(int(round(steuer * 100, 0)))
            + "%\nBrutto",
            0,
            "L",
            fill=True,
        )
        self.set_y(45)
        sum = float(data["ticketPreis"])
        brutto = convertCurrency("{:,.2f} €".format(sum))
        mwst = convertCurrency("{:,.2f} €".format(sum * steuer))
        netto = convertCurrency("{:,.2f} €".format(sum * (1 + steuer)))
        self.multi_cell(
            0,
            6,
            f'{str(data["kWp"])} kWp \n{str(data["gewinnTicket"])} kwp \n{str(round(data["kWp"] + data["gewinnTicket"],2))} kWp \n \n{brutto}\n{mwst}',
            0,
            "R",
        )
        self.set_y(80)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, netto, 0, 0, "R")
        self.line(175, 80, 200, 80)
        # Verbindlichkeiten
        self.set_y(90)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Verbindlichkeiten", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(95)
        self.cell(0, 6, "Das vorliegende Angebot ist gültig bis zum:", 0, 0, "L")
        self.set_x(115)
        self.cell(0, 6, data["gueltig"], 0, 0, "L")
        # Vollmacht
        self.set_y(105)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Vollmacht", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(110)
        self.multi_cell(0, 6, "Zur Realisierung des Projektes, zur Anmeldung der Photovoltaik-Anlage beim Netzbetreiber, zur Registrierung der Photovoltaik-Anlage bei der Bundesnetzagentur, etc. erteilt der Auftraggeber dem Auftragnehmer eine Vollmacht gem. Anlage.", 0, 0, "L")  # type: ignore
        # Garantiebediungen
        self.set_y(125)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Garantiebedingungen", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(130)
        self.multi_cell(0, 6, "Die Garantie der Hardware richtet sich nach den gültigen Garantiebedingungen des jeweiligen Herstellers.", 0, 0, "L")  # type: ignore
        # Auftragserteilung
        self.set_y(140)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Auftragserteilung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(145)
        self.multi_cell(0, 6, "Die oben stehenden Angebotsdetails werden akzeptiert und der Auftrag nach Prüfung der technischen Machbarkeit erteilt. Bis zur vollständigen Zahlung verbleibt das Eigentum an der Photovoltaik-Anlage beim Auftragnehmer. Der Auftraggeber tritt bis dahin die Ansprüche aus der Einspeisevergütung an den Auftragnehmer ab. Des Weiteren gestattet der Auftragnehmer bis zur vollständigen Zahlung dem Auftraggeber, die Photovoltaik-Anlage kostenfrei auf den Dachflächen zu belassen und zu betreiben.", 0, 0, "L")  # type: ignore
        self.set_y(175)
        self.multi_cell(0, 6, "Die Installation der Photovoltaikanlage erfolgt an einem Zählpunkt. Besitzt der Auftraggeber mehrere Stromzähler bzw. Zählpunkte (z.B. für eine Wärmepumpe) und möchte diese zusammenlegen, bietet der Auftragnehmer die Abmeldung verschiedener Zählpunkte beim Netzbetreiber an. Nach dem Ausbau der abgemeldeten Stromzähler durch den Netzbetreiber bleiben die dort installierten Verbraucher stromlos! Das erneute Verdrahten der stromlosen Verbraucher ist kein Bestandteil des hier vorliegenden Auftrags. Der Auftraggeber organisiert eigenständig Fachpersonal, welches die Verdrahtung durchführt.", 0, 0, "L")  # type: ignore
        # # Zahlungsmodalitäten
        # self.set_y(210)
        # self.set_font('JUNO Solar Lt', 'B', 12)
        # self.cell(0, 6, "Zahlungsmodalitäten", 0, 0, 'L')
        # self.set_font('JUNO Solar Lt', '', 11)
        # self.set_y(215)
        # self.multi_cell(0, 6,"20% bei Auftragsbestätigung\n70% bei Baubeginn\n10% bei Netzanschluss",0, 0, 'L')
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


def createTicketPdf(data):
    global title, pages
    title = f"Kalkulation-{data['kunde']}"

    pdf = PDF()
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")

    # create the ticket-PDF
    pdf.page1(data)
    pdf.lastPage(data)

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content
