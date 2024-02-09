from vertrieb_interface.telegram_logs_sender import send_message_to_bot
import datetime
from config.settings import OPENAI_API_KEY, ASSISTANT_ID

def log_and_notify(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")
    send_message_to_bot(message)


# start_chat_log = [
#     {
#         "role": "system",
#         "content": """  
# Titel: Assistent für Solarkraftwerkstechnik
# Rolle: Als spezialisierter KI-Assistent im Bereich Solarkraftwerkstechnik biete ich umfassendes Fachwissen zu Solarmodulen, Installationen und zugehörigen Prozessen.
#             """,
#     }
# ]

# assistant_id = 'asst_9qmpF2KEinRdIIvZC3K2N2Hn'

# # The prompt you want to send to the assistant
# prompt_text = 'Hallo, ich möchte eine Frage zu Solarmodulen und Solartechnik stellen'
# client = OpenAI(api_key=OPENAI_API_KEY)

# assistant = client.beta.assistant.create(
#     name = "",
#     instructions = "",
#     tools = [{"type":""}],
#     model = "gpt-4-1106-preview"
# )

# thread = client.beta.threads.create()
# print(thread)

# messages = client.beta.threads.messages.create(
#     thread_id = thread.id,
#     role = "user",
#     content = ""
# )
# chat_log = None
# completion = openai.ChatCompletion()


# def ask(question, chat_log=None):
#     if chat_log is None:
#         chat_log = start_chat_log
#     prompt2 = [{"role": "user", "content": f"{question}"}]
#     prompt = chat_log + prompt2

#     response = completion.create(  # type: ignore
#         messages=prompt,
#         model="gpt-4",
#     )
#     answer = [response.choices[0].message]  # type: ignore
#     return answer


# def append_interaction_to_chat_log(question, answer, chat_log):
#     if chat_log is None:
#         chat_log = start_chat_log
#     prompt2 = [{"role": "user", "content": f"{question}"}]
#     return chat_log + prompt2 + answer


# def handle_message(text):
#     try:
#         global chat_log
#         question = f"{text}"

#         response = ask(question, chat_log)
#         chat_log = append_interaction_to_chat_log(question, response, chat_log)
#         log_and_notify(f"\n\nUser {text}\n**********AI: {response}")

#         return response[0].content

#     except Exception as e:
#         chat_log = start_chat_log
#         return f"Wait a minute please....{e}"


# def get_chat_bot_response(question, chat_log=None):
#     if chat_log is None:
#         chat_log = start_chat_log
#     prompt2 = [{"role": "user", "content": f"{question}"}]
#     prompt = chat_log + prompt2

#     response = completion.create(
#         messages=prompt,
#         model="gpt-4",
#     )
#     answer = [response.choices[0].message]  # type: ignore
#     return answer
from openai import OpenAI
import time


assistant_id = ASSISTANT_ID

client = OpenAI(api_key=OPENAI_API_KEY)
my_assistant = client.beta.assistants.retrieve(assistant_id)

def handle_message(message, thread_id=None):

    try:
        my_assistant = client.beta.assistants.retrieve(assistant_id)

        if thread_id is None:
           
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            )
            thread_id = thread.id
        else:
            
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role='user',    
                content=message
            )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=my_assistant.id
        )

        while run.status != 'completed':
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            time.sleep(5) 

        thread_messages = client.beta.threads.messages.list(thread_id)

       
        for msg in thread_messages.data:
            if msg.role == 'assistant': 
                
                return msg.content[0].text.value, thread_id

    except Exception as e:
        # Log the exception here if necessary, e.g., print(e) or logging.error(e)
        error_message = f"An error occurred: {e}"
        # Return the error message and None or a default value for thread_id
        return error_message, thread_id