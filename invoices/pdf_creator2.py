from math import ceil
from datetime import datetime, date
from fpdf import FPDF
import os
from config import settings
from config.settings import STATIC_URL
from prices.models import ElektrikPreis

import os

title = ""
pages = "2"


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
        # Line break
        self.ln(15)

    def footer(self):
        # Arial italic 8
        self.set_font("JUNO Solar Lt", "", 8)
        # Text color in gray
        self.set_text_color(128)
        # Position at 1.5 cm from bottom
        self.set_y(-30)
        self.multi_cell(
            0,
            5,
            "Geschäftsführer: Denny Schädlich\npersönlich haftender Gesellschaftler: Juno Solar Home Verwaltungs GmbH\nSitz Werdau ∙ Amtsgericht Chemnitz HRB 34192 ∙ Steuernummer 227/156/19508 ∙ Ust-IdNr DE 34514953",
            0,
            0,  # type: ignore
            "L",  # type: ignore
        )
        self.set_y(-30)
        self.set_x(150)
        self.multi_cell(
            0,
            5,
            "Commerzbank Chemnitz\nIBAN DE94 8704 0000 0770 0909 00\nBIC/Swift-Code: COBADEFFXXX",
            0,
            "R",
        )

    def page1(self, eintrag, user, k_data, mats):
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
        for data in k_data:
            self.multi_cell(
                0,
                5,
                f"{data.kunden_name}\n{data.kunden_strasse}\n{data.kunden_plz_ort}",
                0,
                0,  # type: ignore
                "L",  # type: ignore
            )
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
        self.multi_cell(
            0,
            5,
            f"{user.first_name} {user.last_name}\n{user.phone}\n{user.email}\n\nwww.juno-solar.com",
            0,
            "R",
        )
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
        # self.multi_cell(0, 5, "Gesamtleistung der Anlage:\nStandort der Anlage:", 0, '')
        self.set_y(100)
        self.set_x(70)
        # self.multi_cell(0, 5, f'{"----"} kWp\n{mat_0.standort}', 0, 'L')
        self.set_y(100)
        for data in k_data:
            self.cell(0, 6, f"{data.kunden_name},", 0, 0, "L")
        self.set_x(0)
        self.set_y(115)
        self.multi_cell(
            0,
            5,
            "vielen Dank für Ihre Anfrage. Wir bieten Ihnen Wechselstromseitige Installation und Inbetriebnahme:",
            0,
            "",
        )
        # Tabelle Beginn
        self.set_font("JUNO Solar Lt", "B", 12)
        self.set_x(0)
        self.set_y(125)
        self.cell(0, 6, "Pos.", 0, 0, "L")
        self.set_x(25)
        self.cell(0, 6, "Bezeichnung", 0, 0, "L")
        self.set_x(150)
        self.cell(0, 6, "Menge", 0, 0, "L")
        self.set_x(170)
        self.cell(0, 6, "Gesamtpreis", 0, 0, "R")
        # Gleichstromseitige Installation
        self.line(10, 131, 200, 131)
        self.set_y(134)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(
            0, 6, "Wechselstromseitige Installation und Inbetriebnahme", 0, 0, "L"
        )
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(135)
        self.multi_cell(
            0,
            5,
            "\nDie wechselstromseitige Installation beschreibt sämtliche Bauteile sowie Dienstleistungen, die sich im Wechselstromkreisbefinden. Die Installation des Wechselrichters stellt hierbei den Schnittpunkt zur gleichstromseitigen Installation dar. Kundenseitig stellt der Zählerschrank bzw. die Übergabestation die Schnittstelle zum Energieversorger dar.",
            0,
            "L",
        )
        # Tabelle Eintrag 1
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(160)
        eintrag += 1
        self.cell(0, 6, str(eintrag) + ".", 0, 0, "L")
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "B", 10)
        self.cell(0, 5, "Komplettpaket Zahlerschrank bestehend aus:", 0, 0, "L")

        self.set_y(165)
        self.set_x(25)
        self.set_font("JUNO Solar Lt", "", 10)
        for position in mats:
            model_name = f"{position.position}"
            quantity = str(position.quantity).strip("Decimal()")
            self.set_x(25)
            self.multi_cell(0, 5, f"∙ {model_name}", 0, "L")
        self.set_y(165)
        self.set_x(150)
        self.set_font("JUNO Solar Lt", "", 10)
        for position in mats:
            model_name = f"{position.position}"
            if (
                "Mantellleitung" in model_name
                or "Kabelschellen" in model_name
                or "Kabelkanal" in model_name
                or "H07-VK" in model_name
            ):
                quantity = str(position.quantity).strip("Decimal()") + "  m"
            else:
                quantity = str(position.quantity).strip("Decimal()") + "  stk."
            self.set_x(150)
            self.multi_cell(0, 5, f"- {quantity}", 0, "L")

        return eintrag

    def lastPage(self, eintrag, total_summe):
        self.add_page()

        # Angebotssumme
        self.set_fill_color(240)
        self.set_y(35)
        self.set_font("JUNO Solar Lt", "B", 17)
        self.multi_cell(0, 6, "Angebotssumme\n ", 0, "L", fill=True)
        self.set_font("JUNO Solar Lt", "", 12)
        self.set_y(45)
        steuer = "0"
        self.multi_cell(
            0,
            6,
            "Anlagengröße\n \nNetto\nMwSt. " + steuer + "%\nBrutto",
            0,
            "L",
            fill=True,
        )
        self.set_y(45)
        sum = total_summe
        brutto = f"{sum} €"
        mwst = "0 €"
        netto = f"{sum} €"
        self.multi_cell(0, 6, f"\n \n{brutto}\n{mwst}", 0, "R")
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
        self.cell(0, 6, "gueltig", 0, 0, "L")
        # Vollmacht
        self.set_y(95)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Vollmacht", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(100)
        self.multi_cell(
            0,
            6,
            "Zur Realisierung des Projektes, zur Anmeldung der Photovoltaik-Anlage beim Netzbetreiber, zur Registrierung der Photovoltaik-Anlage bei der Bundesnetzagentur, etc. erteilt der Auftraggeber dem Auftragnehmer eine Vollmacht gem. Anlage.",
            0,
            0,  # type: ignore
            "L",  # type: ignore
        )
        # Garantiebediungen
        self.set_y(115)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Garantiebedingungen", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(120)
        self.multi_cell(
            0,
            6,
            "Die Garantie der Hardware richtet sich nach den gültigen Garantiebedingungen des jeweiligen Herstellers.",
            0,
            0,  # type: ignore
            "L",  # type: ignore
        )
        # Auftragserteilung
        self.set_y(130)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Auftragserteilung", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(135)
        self.multi_cell(
            0,
            6,
            "Die oben stehenden Angebotsdetails werden akzeptiert und der Auftrag nach Prüfung der technischen Machbarkeit erteilt. Bis zur vollständigen Zahlung verbleibt das Eigentum an der Photovoltaik-Anlage beim Auftragnehmer. Der Auftraggeber tritt bis dahin die Ansprüche aus der Einspeisevergütung an den Auftragnehmer ab. Des Weiteren gestattet der Auftragnehmer bis zur vollständigen Zahlung dem Auftraggeber, die Photovoltaik-Anlage kostenfrei auf den Dachflächen zu belassen und zu betreiben.",
            0,
            0,  # type: ignore
            "L",  # type: ignore
        )
        self.set_y(165)
        self.multi_cell(
            0,
            6,
            "Die Installation der Photovoltaikanlage erfolgt an einem Zählpunkt. Besitzt der Auftraggeber mehrere Stromzähler bzw. Zählpunkte (z.B. für eine Wärmepumpe) und möchte diese zusammenlegen, bietet der Auftragnehmer die Abmeldung verschiedener Zählpunkte beim Netzbetreiber an. Nach dem Ausbau der abgemeldeten Stromzähler durch den Netzbetreiber bleiben die dort installierten Verbraucher stromlos! Das erneute Verdrahten der stromlosen Verbraucher ist kein Bestandteil des hier vorliegenden Auftrags. Der Auftraggeber organisiert eigenständig Fachpersonal, welches die Verdrahtung durchführt.",
            0,
            0,  # type: ignore
            "L",  # type: ignore
        )
        # Zahlungsmodalitäten
        self.set_y(200)
        self.set_font("JUNO Solar Lt", "B", 12)
        self.cell(0, 6, "Zahlungsmodalitäten", 0, 0, "L")
        self.set_font("JUNO Solar Lt", "", 11)
        self.set_y(205)
        self.multi_cell(
            0,
            6,
            "20% bei Auftragsbestätigung\n70% bei Baubeginn\n10% bei Netzanschluss",
            0,
            0,  # type: ignore
            "L",  # type: ignore
        )
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


def createOfferPdf(invoice, eintrag, user, mats, k_data):
    total_position_price = []

    for position in mats:
        name = f"{position.position}"
        quantity = str(position.quantity).strip("Decimal()")
        kabel_price = ElektrikPreis.objects.get(name=name).price
        total_price = float(kabel_price) * float(quantity)
        total_position_price.append(total_price)

    total_summe = sum(total_position_price)
    global title, pages

    title = f"{invoice.invoice_id}"
    pages = "2"
    pdf = PDF()
    pdf.set_title(title)
    pdf.set_author("JUNO Solar Home GmbH")

    # Create the offer-PDF
    eintrag = 0
    eintrag = pdf.page1(eintrag, user, k_data, mats)
    # eintrag = pdf.page2(data, eintrag)
    # eintrag = pdf.page3(data, eintrag)
    # pdf.page4_durchgestrichen(data, eintrag)
    pdf.lastPage(eintrag, total_summe)

    # Generate the PDF and return it
    pdf_content = pdf.output(dest="S").encode("latin1")  # type: ignore
    return pdf_content


# def createOfferPdf(
#     invoice,
#     eintrag,
#     user,
#     mats,
#     k_data,
# ):
#     total_position_price = []

#     for position in mats:
#         name = f"{position.position}"
#         quantity = str(position.quantity).strip("Decimal()")
#         kabel_price = ElektrikPreis.objects.get(name=name).price
#         total_price = float(kabel_price) * float(quantity)
#         total_position_price.append(total_price)

#     total_summe = sum(total_position_price)
#     global title, pages

#     title = f"{invoice.invoice_id}"
#     pages = "2"
#     pdf = PDF()
#     pdf.set_title(title)
#     pdf.set_author("JUNO Solar Home GmbH")

#     # create the offer-PDF
#     eintrag = 0
#     eintrag = pdf.page1(eintrag, user, k_data, mats)
#     # eintrag = pdf.page2(data, eintrag)
#     # eintrag = pdf.page3(data, eintrag)
#     # pdf.page4_durchgestrichen(data, eintrag)
#     pdf.lastPage(eintrag, total_summe)

#     # set path of the PDF
#     user_folder = os.path.join(
#         settings.MEDIA_ROOT, f"pdf/usersangebots/{user.username}/"
#     )

#     # Create the directory if it doesn't exist
#     if not os.path.exists(user_folder):
#         os.makedirs(user_folder)

#     # Save the PDF file
#     output_file = os.path.join(user_folder, f"Angebot_{invoice.invoice_id}.pdf")

#     # create the directory if needed
#     if not os.path.exists(user_folder):
#         os.makedirs(user_folder)
#         outputPath = os.path.join(user_folder, f"Angebot_{invoice.invoice_id}.pdf")
#     pdf.output(output_file, "F")
