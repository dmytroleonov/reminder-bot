import logging
import sys

# Load environment variables and setup logger before importing the modules that use them
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s]: [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

from src.bot import bot  # noqa: E402
from src.scheduler import scheduler  # noqa: E402


def main():
    scheduler.start()
    logger.info("Starting the bot...")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
