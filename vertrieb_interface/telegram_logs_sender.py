import telebot
from telebot import apihelper
from dotenv import load_dotenv
from config.settings import ENV_FILE, TELEBOT_TOKEN, CHAT_ID

load_dotenv(ENV_FILE)


bot = telebot.TeleBot(TELEBOT_TOKEN)


@bot.message_handler(commands=["getid"])
def handle_getid(message):
    try:
        bot.reply_to(message, f"Your chat ID is: {message.chat.id}")
    except Exception as e:
        print(f"Error while replying with chat ID: {e}")


def send_message_to_bot(text):
    """
    Send a message to a specified Telegram chat using a bot.

    Parameters:
    - text (str): The message text to send.
    - chat_id (int or str): The chat ID where the message should be sent.
    """
    try:
        bot.send_message(CHAT_ID, text)
    except apihelper.ApiException as e:
        print(f"Telegram API error: {e}")
    except Exception as e:
        print(f"Error sending message: {e}")


# Funktion zum Senden von Benachrichtigungen mit verbesserter Nachrichtenstruktur
def send_custom_message(user, action, details):

    user_name = f"{user.first_name} {user.last_name}".strip()
    user_name = user_name if user_name else "Ein Benutzer"

    message = f"{user_name} {action} {details}"
    send_message_to_bot(message)
