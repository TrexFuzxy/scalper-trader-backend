from telegram import Bot
import os

def send_telegram_signal(token, chat_id, signal, image_path):
    bot = Bot(token=token)
    with open(image_path, 'rb') as img:
        bot.send_photo(chat_id=chat_id, photo=img, caption=str(signal)) 