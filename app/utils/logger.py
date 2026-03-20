import logging
import os
from logging.handlers import RotatingFileHandler
from .config import config

def setup_logger():
    # Ensure logs directory exists
    os.makedirs("data/logs", exist_ok=True)
    
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        "data/logs/bot.log", 
        maxBytes=5*1024*1024, # 5MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    return logging.getLogger("DealRadar")

logger = setup_logger()
