import openai
# from config.settings import OPENAI_API_KEY

OPENAI_API_KEY="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"
openai.api_key = OPENAI_API_KEY

start_chat_log = [
    {
        "role": "system",
        "content": 
                    """  
                    Schlüpfen Sie in die Rolle eines Elektroingenieurs in der Solarenergiebranche. 
                    Ihre Aufgabe ist es, die grundlegendsten und wichtigsten Thesen(2-3 max) aus dem [Text] auszuwählen, die nur Informationen über die Anlage betreffen, und sie so kurz und klar wie möglich zu schreiben. Versuchen Sie, die Anzahl der Thesen so gering wie möglich zu halten, ohne jedoch die Hauptaussagen des Textes zu verlieren. 
                    Schreiben Sie nur die These, ohne zusätzlichen Text oder Erklärungen. 
                    Diese Thesen werden dem Plan für die Solaranlage beigefügt.
                    """
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
        temperature=0.54,
        model="gpt-4",
    )
    answer = [response.choices[0].message]  # type: ignore
    return answer

def handle_message(text):
    try:
        global chat_log
        question = f"[Text]: {text}"
        response = ask(question, chat_log)
        print(response[0].content)
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
        temperature=0.54,
        model="gpt-4",
    )
    answer = [response.choices[0].message]  # type: ignore
    return answer

