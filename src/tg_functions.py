import base64
import sqlite3
from io import BytesIO
from pathlib import Path

import telebot

from src.settings import TG_BOT_API

# Initialize bot with your token
bot = telebot.TeleBot(TG_BOT_API)


def save_photo(message):
    # создадим папку если её нет
    Path(f'files/{message.chat.id}/photos').mkdir(parents=True, exist_ok=True)

    # сохраним изображение
    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file = BytesIO(downloaded_file)
    binary = base64.b64encode(file.getvalue()).decode()
    return binary
