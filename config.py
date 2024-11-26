import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

# database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_LITE = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'users.db')}"

# bot config from env file
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")
BOT_ID = os.getenv("BOT_ID")

FAKE_BIDS = 752
MAX_BIDS = 3
MONEY_AMOUNT = 0.5
MIN_BALANCE_CRYPTO = 5