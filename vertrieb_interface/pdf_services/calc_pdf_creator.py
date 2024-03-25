import os
import platform
import traceback
import matplotlib.pyplot as plt
from config import settings
from matplotlib.figure import Figure
from datetime import date
from vertrieb_interface.pdf_services.helper_functions import printFloat
from fpdf import FPDF

title = ""
pages = "2"


class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super(PDF, self).__init__(*args, **kwargs)
        self.set_left_margin(18.875)
        self.set_right_margin(12.875)

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
        pass

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
        self.multi_cell(0, 5, f'{data["firma"]}\n{data["anrede"]} {data["kunde"]}\n{data["adresse"]}', 0, 0, "L")  # type: ignore
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
        self.cell(0, 6, "Unverbindliche Kostengegenüberstellung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_x(0)
        self.set_y(y + 10)
        self.cell(0, 5, f'Werdau, {date.today().strftime("%d.%m.%Y")}', 0, 0, "L")
        self.set_x(0)
        self.set_y(y + 20)
        self.multi_cell(
            0,
            5,
            "Die errechneten Energiegewinne in der folgenden Kostengegenüberstellung beruhen auf empirisch ermittelten Daten. Je nach Nutzerverhalten und Witterungsverhältnissen werden die prognostizierten Energieerträge von der Praxis abweichen.",
            0,
            "",
        )
        # Ausgangsdaten
        y += 35
        self.line(18, y + 5, 48, y + 5)
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "B", 13)
        self.cell(0, 6, "Ausgangsdaten", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y + 10)
        self.cell(0, 5, "Stromverbrauch pro Jahr", 0, 0, "L", fill=True)
        self.cell(0, 5, f"{data['stromverbrauch']} kWh", 0, 0, "R", fill=True)
        # Strom Grundpreis
        y += 20
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y)
        self.cell(0, 5, "Strom Grundpreis [brutto]", 0, 0, "L", fill=True)
        self.set_y(y + 5)
        self.set_font("JUNO Solar Lt", "", 10)
        self.cell(
            0, 5, "entsprechend der Angabe des Interessenten", 0, 0, "L", fill=True
        )
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 5, f"{data['grundpreis']} €/Monat".replace(".", ","), 0, 0, "R")
        # Strom Arbeitspreis
        y += 15
        self.set_y(y)
        self.cell(0, 5, "Strom Arbeitspreis [brutto]:", 0, 0, "L", fill=True)
        self.set_y(y + 5)
        self.set_font("JUNO Solar Lt", "", 10)
        self.cell(
            0, 5, "entsprechend der Angabe des Interessenten", 0, 0, "L", fill=True
        )
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 5, f"{data['arbeitspreis']} ct/kWh".replace(".", ","), 0, 0, "R")
        # Prognose Strompreiserhöhung pro Jahr [%]:
        y += 15
        self.set_y(y)
        self.cell(
            0, 5, "Prognose Strompreiserhöhung pro Jahr [%]:", 0, 0, "L", fill=True
        )
        self.cell(0, 5, f"{data['prognose']} %", 0, 0, "R")
        # Berechnungszeitraum [Jahre]:
        y += 10
        self.set_y(y)
        self.cell(0, 5, "Berechnungszeitraum [Jahre]:", 0, 0, "L", fill=True)
        self.cell(0, 5, f"{data['zeitraum']} Jahre", 0, 0, "R")
        # Energiespeicher:
        y += 10
        self.set_y(y)
        self.cell(0, 5, "Energiespeicher:", 0, 0, "L", fill=True)
        batt = "Nein"
        if data["batterieVorh"]:
            batt = "Ja"
        self.cell(0, 5, batt, 0, 0, "R")
        # Ausrichtung PV-Anlage:
        y += 10
        self.set_y(y)
        self.cell(0, 5, "Ausrichtung PV-Anlage:", 0, 0, "L", fill=True)
        self.cell(0, 5, f"{data['ausrichtung']}", 0, 0, "R")
        # Einspeisevergütung
        y += 10
        self.line(18, y + 5, 52, y + 5)
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "B", 13)
        self.cell(0, 6, "Einspeisevergütung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y + 10)
        self.cell(0, 5, "bis 10 kWp", 0, 0, "L", fill=True)
        self.cell(
            0, 5, f"{data['bis10kWp']} ct/kWh".replace(".", ","), 0, 0, "R", fill=True
        )
        self.set_y(y + 20)
        self.cell(0, 5, "10-40 kWp", 0, 0, "L", fill=True)
        self.cell(
            0, 5, f"{data['10bis40kWp']} ct/kWh".replace(".", ","), 0, 0, "R", fill=True
        )

    def page2(self, data, user_folder, vertrieb_angebot):
        self.add_page()
        self.set_fill_color(240)
        # Kostenkalkulation ohne Photovoltaikanlage anhand der Ausgangsdaten
        y = 35
        self.line(18, y + 5, 136, y + 5)
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "B", 13)
        self.cell(
            0,
            6,
            "Kostenkalkulation ohne Photovoltaikanlage anhand der Ausgangsdaten",
            0,
            0,
            "L",
        )
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(y + 10)
        self.cell(0, 5, "Grundpreis:", 0, 0, "L", fill=True)
        # Berechnung des Grundpreises des Stromvertrags
        self.cell(
            0,
            5,
            f"{printFloat(data['grundpreisGes'])} €".replace(".", ","),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 20)
        self.cell(0, 5, "Arbeitspreis:", 0, 0, "L", fill=True)
        # Berechnung des Arbeitspreises ohne PV-Anlage
        self.cell(
            0,
            5,
            f"{printFloat(data['arbeitspreisGes'])} €".replace(".", ","),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 30)
        self.cell(
            0,
            5,
            "Summe [entsprechend dem oben angegeben Zeitraum]:",
            0,
            0,
            "L",
            fill=True,
        )
        self.set_font("JUNO Solar Lt", "B", 11)
        self.cell(
            0,
            5,
            f"{printFloat(data['arbeitspreisGes']+data['grundpreisGes'])} €".replace(
                ".", ","
            ),
            0,
            0,
            "R",
            fill=True,
        )
        self.line(170, y + 35, 200, y + 35)
        self.line(170, y + 36, 200, y + 36)
        # Kostenkalkulation mit Photovoltaikanlage anhand der Ausgangsdaten
        y += 40
        self.line(18, y + 5, 135, y + 5)
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "B", 13)
        self.cell(
            0,
            6,
            "Kostenkalkulation mit Photovoltaikanlage anhand der Ausgangsdaten",
            0,
            0,
            "L",
        )
        self.set_font("JUNO Solar Lt", "B", 11)
        self.set_y(y + 10)
        self.cell(0, 5, "Gesamtleistung der PV-Anlage:", 0, 0, "L", fill=True)
        self.cell(0, 5, f"{data['kWp']} kWp".replace(".", ","), 0, 0, "R", fill=True)
        self.set_y(y + 20)
        self.cell(0, 5, "generierte PV-Energie pro Jahr:", 0, 0, "L", fill=True)
        self.cell(
            0,
            5,
            f"{data['erzeugteEnergie']} kWh".replace(".", ","),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 30)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(0, 5, "davon nutzbare Energie:", 0, 0, "L", fill=True)
        self.cell(
            0,
            5,
            f"{printFloat(data['nutzEnergie'])} kWh".replace(".", ","),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 40)
        self.cell(0, 5, "davon eingespeiste Energie:", 0, 0, "L", fill=True)
        self.cell(
            0,
            5,
            f"{printFloat(data['erzeugteEnergie']-data['nutzEnergie'])}kWh".replace(
                ".", ","
            ),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 50)
        self.set_font("JUNO Solar Lt", "B", 11)
        self.cell(
            0, 5, "benötigte Restenergie aus dem Stromnetz:", 0, 0, "L", fill=True
        )
        self.cell(
            0,
            5,
            f"{printFloat(data['restenergie'])} kWh".replace(".", ","),
            0,
            0,
            "R",
            fill=True,
        )
        # Doppelabsatz dazwischen
        y += 65
        self.set_y(y)
        self.set_font("JUNO Solar Lt", "", 11)
        self.cell(
            0, 5, "Gesamtpreis für PV-Anlage (inkl. Montage):", 0, 0, "L", fill=True
        )
        self.cell(
            0,
            5,
            f"{printFloat(data['kostenPVA'])}€".replace(".", ","),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 10)
        self.cell(0, 5, "Kosten für benötigten Reststrom:", 0, 0, "L", fill=True)
        self.cell(
            0,
            5,
            f"{printFloat(data['reststromPreis'] + data['grundpreisGes'])} €".replace(
                ".", ","
            ),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 20)
        self.cell(0, 5, "Einspeisevergütung insgesamt:", 0, 0, "L", fill=True)
        self.cell(
            0,
            5,
            f"{printFloat(data['einspVerg'])} €".replace(".", ","),
            0,
            0,
            "R",
            fill=True,
        )
        self.set_y(y + 30)
        self.set_font("JUNO Solar Lt", "B", 11)
        self.cell(0, 5, "Erparnis durch eine PV-Anlage:", 0, 0, "L", fill=True)
        self.set_y(y + 35)
        self.set_font("JUNO Solar Lt", "", 10)
        self.cell(
            0, 5, "bezogen auf den oben angegebenen Zeitraum", 0, 0, "L", fill=True
        )
        self.set_y(y + 30)
        self.set_font("JUNO Solar Lt", "B", 11)
        self.cell(
            0, 5, f"{printFloat(data['ersparnis'])} €".replace(".", ","), 0, 0, "R"
        )
        self.line(170, y + 35, 200, y + 35)
        self.line(170, y + 36, 200, y + 36)
        # Grafik der Amortisationszeit
        X = list(range(data["zeitraum"]))
        y1 = data["arbeitsListe"]
        y2 = data["restListe"]
        try:
            fig = Figure(figsize=(10, 5))
            ax = fig.add_subplot()
            ax.plot(X, y1, color="r", label="ohne PVA")
            ax.plot(X, y2, color="g", label="mit PVA")
            ax.set_xlabel("Jahre")
            ax.set_ylabel("Kosten in €")
            ax.set_title("Visualisierung der voraussichtlichen Amortisationszeit")
            ax.legend()

            ax.figure.savefig(
                f"{user_folder}/calc_tmp_{vertrieb_angebot.angebot_id}.png"
            )
            self.image(
                f"{user_folder}/calc_tmp_{vertrieb_angebot.angebot_id}.png",
                x=10,
                y=185,
                w=200,
            )
            calc_folder = f"{user_folder}/"
            calc_image = f"{user_folder}/calc_tmp_{vertrieb_angebot.angebot_id}.png"
        except Exception as e:
            print(e)


def createCalcPdf(data, vertrieb_angebot, user):
    global title, pages
    title = f"Kalkulation-{data['kunde']}"

    pdf = PDF()
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")

    user_folder = os.path.join(
        settings.MEDIA_ROOT, f"pdf/usersangebots/{user.username}/Kalkulationen/"
    )
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    # create the calc-PDF
    pdf.page1(data)
    pdf.page2(data, user_folder, vertrieb_angebot)

    output_file = os.path.join(
        user_folder, f"Kalkulation_{vertrieb_angebot.angebot_id}.pdf"
    )

    # create the directory if needed
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
        outputPath = os.path.join(
            user_folder, f"Kalkulation_{vertrieb_angebot.angebot_id}.pdf"
        )
    pdf.output(output_file, "F")


def createCalcPdf2(data, vertrieb_angebot, user):
    global title, pages
    title = f"{vertrieb_angebot.angebot_id}"
    pages = "5"
    pdf = PDF()
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")
    user_folder = os.path.join(
        settings.MEDIA_ROOT, f"pdf/usersangebots/{user.username}/Kalkulationen/"
    )
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    # create the offer-PDF
    pdf.page1(data)
    pdf.page2(data, user_folder, vertrieb_angebot)

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content
