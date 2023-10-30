import openai
from vertrieb_interface.telegram_logs_sender import send_message_to_bot
import datetime
from config.settings import OPENAI_API_KEY
import logging

openai.api_key = OPENAI_API_KEY


def log_and_notify(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")
    send_message_to_bot(message)


start_chat_log = [
    {
        "role": "system",
        "content": """  
Titel: Assistent für Solarkraftwerkstechnik
Rolle: Als spezialisierter KI-Assistent im Bereich Solarkraftwerkstechnik biete ich umfassendes Fachwissen zu Solarmodulen, Installationen und zugehörigen Prozessen.
Aufgaben:
Erklären Sie verschiedene Solarmodule inkl. Vor- und Nachteile, Leistung, Lebensdauer und Effizienz.
Unterstützen Sie bei der Planung und Installation von Solarenergiesystemen, inkl. Standortwahl, Modulpositionierung, Systemdimensionierung und Komponentenauswahl.
Beantworten Sie technische Fragen zu Installation und Sicherheit sowie Lösungen für häufige Installationsprobleme.
Erklären Sie Funktionen und Unterschiede von Solarkraftwerkskomponenten wie Modulen, Wechselrichtern, Batterien und Verkabelung.
Informieren Sie über Wartungsroutinen, Fehlersuche, Leistungsüberwachung und Reinigungsmethoden.
Halten Sie sich auf dem Laufenden über Normen, Zertifikate und Vorschriften der Branche.
Geben Sie Einblicke in die neuesten Fortschritte und deren Auswirkungen auf die Branche.
Zusätzliche Qualitäten:
Klare, prägnante und geduldige Antworten.
Aufbereitung komplexer technischer Informationen.
Ständige Aktualisierung von Trends, Technologien und Praktiken.
Berücksichtigung von Umweltbelangen und Energieeffizienz.
Verständnis für wirtschaftliche Aspekte von Solarkraftwerken.
Ziel:
Seien Sie eine umfassende Ressource und bieten Sie praktische Hilfe für Elektriker und Benutzer im Bereich Solarkraftwerkstechnik.",
            """,
    }
]

chat_log = None
completion = openai.ChatCompletion()


def ask(question, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    prompt2 = [{"role": "user", "content": f"{question}"}]
    prompt = chat_log + prompt2

    response = completion.create(  # type: ignore
        messages=prompt,
        model="gpt-4",
    )
    answer = [response.choices[0].message]  # type: ignore
    return answer


def append_interaction_to_chat_log(question, answer, chat_log):
    if chat_log is None:
        chat_log = start_chat_log
    prompt2 = [{"role": "user", "content": f"{question}"}]
    return chat_log + prompt2 + answer


def handle_message(text):
    try:
        global chat_log
        question = f"{text}"

        response = ask(question, chat_log)
        chat_log = append_interaction_to_chat_log(question, response, chat_log)
        log_and_notify(f"\n\nUser {text}\n**********AI: {response}")

        return response[0].content

    except Exception as e:
        chat_log = start_chat_log
        return f"Wait a minute please....{e}"


def get_chat_bot_response(question, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    prompt2 = [{"role": "user", "content": f"{question}"}]
    prompt = chat_log + prompt2

    response = completion.create(
        messages=prompt,
        model="gpt-4",
    )
    answer = [response.choices[0].message]  # type: ignore
    return answer
