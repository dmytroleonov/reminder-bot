from functools import wraps
import logging
import os

from telebot.types import Message

from src.bot.config import bot
from src.bot.constants import COMMAND_NOT_ALLOWED

logger = logging.getLogger(__name__)

ALLOWED_CHAT_IDS_STR = (os.environ.get("ALLOWED_CHAT_IDS") or "-1").split(",")
ALLOWED_CHAT_IDS = list(map(int, ALLOWED_CHAT_IDS_STR))


def protected(func):
    @wraps(func)
    def wrapper(message: Message):
        if message.chat.id not in ALLOWED_CHAT_IDS:
            logger.warning(
                f"Attempt at unauthorized access in chat [{message.chat.id}]. "
                f"User: @{message.from_user.username} {message.from_user.full_name}. "
                f"Message: {message.text}."
            )
            bot.send_message(chat_id=message.chat.id, text=COMMAND_NOT_ALLOWED)
            return
        func(message)

    return wrapper
