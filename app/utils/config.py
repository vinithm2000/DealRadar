import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_PATH = os.getenv("DB_PATH", "data/deals.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    EARNKARO_ID = os.getenv("EARNKARO_ID", "YOUR_ID")

config = Config()
