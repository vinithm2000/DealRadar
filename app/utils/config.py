import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_PATH = os.getenv("DB_PATH", "data/deals.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    EARNKARO_ID = os.getenv("EARNKARO_ID", "YOUR_ID")
    EARNKARO_EMAIL = os.getenv("EARNKARO_EMAIL", "")
    EARNKARO_PASSWORD = os.getenv("EARNKARO_PASSWORD", "")
    ADMIN_ID = os.getenv("ADMIN_ID")
    SCHEDULE_INTERVAL_MIN = int(os.getenv("SCHEDULE_INTERVAL_MIN", "15"))

config = Config()
