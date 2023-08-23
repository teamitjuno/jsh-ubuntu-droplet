from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from authentication.models import User
from elektriker_kalender.models import (
    ElectricCalendar,
    PVAKlein1,
)  # Make sure to replace "your_app" with the name of your Django app
import random


def create_instances(data_list, kurz):
    for item in data_list:
        data = item["data"]
        zoho_id = str(
            data["Elektriker_calfield"]
        )  # Convert ID to string since zoho_id is a CharField

        try:
            # Try to get User by zoho_id
            user = User.objects.get(zoho_id=zoho_id)
        except ObjectDoesNotExist:
            # If User does not exist, skip this data
            continue
        try:
            # Try to get ElectricCalendar by zoho_id
            ElectricCalendar.objects.get(zoho_id=data["ID"])
        except ObjectDoesNotExist:
            # If ElectricCalendar does not exist, create a new one
            elektriktermin_am = datetime.strptime(
                data["Elektriktermin_am"], "%d-%b-%Y %H:%M"
            )
            elektriker_calfield = int(data["Elektriker_calfield"])

            calendar = ElectricCalendar(
                calendar_id=generate_angebot_id(str(elektriktermin_am), kurz),
                zoho_id=data["ID"],
                user=user,
                anschluss_PVA=data["Anschluss_PVA"],
                elektriker_calfield=elektriker_calfield,
                kundenname=data["Kundenname"],
                privatkunde_adresse_pva=data["Privatkunde.Adresse_PVA"],
                besonderheiten=data["Besonderheiten"],
                elektriktermin_am=elektriktermin_am,
                kundenname_rawdata=data["Kundenname-rawdata"],
                termin_best_tigt=data["Termin_best_tigt"],
            )
            try:
                calendar.save()
            except Exception as e:
                print(f"Error saving calendar: {e}")

            try:
                pva_klein1 = PVAKlein1(
                    display_value=data["PVA_klein1"]["display_value"],
                    ID=data["PVA_klein1"]["ID"],
                    calendar=calendar,
                )
                pva_klein1.save()
            except Exception as e:
                print(f"Error saving pva_klein1: {e}")


def generate_angebot_id(date_string, kurz):
    if not date_string:
        date_string = random.randint(100000, 999999)
        random_number = random.randint(100000, 999999)
        return f"KALENDER-{kurz}{date_string}-{random_number}"
    else:
        anfrage_vom_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        random_number = random.randint(100000, 999999)
        return f"KALENDER-{kurz}{anfrage_vom_date.strftime('%d%m%Y')}-{random_number}"
