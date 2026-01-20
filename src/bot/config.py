import logging
import os

import telebot

from src.bot import constants

logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_CHAT_IDS = os.environ.get("ALLOWED_CHAT_IDS")

if not TOKEN:
    raise ValueError(constants.NO_BOT_TOKEN)

if not ALLOWED_CHAT_IDS:
    logger.warning(constants.NO_ALLOWED_CHAT_IDS)

bot = telebot.TeleBot(TOKEN)
