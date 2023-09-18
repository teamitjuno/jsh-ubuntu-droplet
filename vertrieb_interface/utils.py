import random
from django.db import transaction
from datetime import datetime
from vertrieb_interface.models import VertriebAngebot


def load_vertrieb_angebot(data, user, kurz):
    try:
        
        with transaction.atomic():
            for item in data:
                if not VertriebAngebot.objects.filter(zoho_id=item["zoho_id"]).exists():
                    # if not item.get("zoho_kundennumer"):
                    #     print(
                    #         f"Missing zoho_kundennumer for {item['name']}, skipping..."
                    #     )
                    #     continue
                    # # Check if a VertriebAngebot with this zoho_kundennumer already exists
                    # elif VertriebAngebot.objects.filter(
                    #     zoho_kundennumer=item["zoho_kundennumer"]
                    # ).exists():
                    #     print(
                    #         f"VertriebAngebot with zoho_kundennumer {item['zoho_kundennumer']} already exists, skipping..."
                    #     )
                    #     continue
                    
                    item["user"] = user
                    item["angebot_id"] = generate_angebot_id(
                        item.get("anfrage_vom"), kurz
                    )
                    email = item.get("email")
                    if not email:
                        item["email"] = "keine@email.com"
                    if (
                        "ü" in item.get("email")
                        or "ö" in item.get("email")
                        or "ä" in item.get("email")
                        or "_" in item.get("email")
                        or item.get("email")[1] == "."
                    ):
                        item["email"] = (
                            item.get("email")
                            .replace("ö", "o")
                            .replace("ä", "a")
                            .replace("ü", "u")
                            .replace("_", "-")
                        )
                    termine_text = item.get("termine_text")

                    try:
                        instance = VertriebAngebot(**item)

                    except:
                        item["email"] = "keine@email.com"
                        instance = VertriebAngebot(**item)

                    

        return "All data has been successfully processed."

    except Exception as e:
        print(f"An error occurred: {e}")
        pass


def generate_angebot_id(date_string, kurz):
    if not date_string:
        date_string = random.randint(100000, 999999)
        random_number = random.randint(100000, 999999)
        return f"AN-{kurz}{date_string}-{random_number}"
    else:
        anfrage_vom_date = datetime.strptime(date_string, "%d-%b-%Y")
        random_number = random.randint(100000, 999999)
        return f"AN-{kurz}{anfrage_vom_date.strftime('%d%m%Y')}-{random_number}"


def create_graph(data):
    import matplotlib.pyplot as plt
    import io

    X = list(range(data["zeitraum"]))
    y1 = data["arbeitsListe"]
    y2 = data["restListe"]

    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot()
    ax.plot(X, y1, color="r", label="ohne PVA")
    ax.plot(X, y2, color="g", label="mit PVA")
    ax.set_xlabel("Jahre")
    ax.set_ylabel("Kosten in €")
    ax.set_title("Visualisierung der voraussichtlichen Amortisationszeit")
    ax.legend()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)

    return buf
