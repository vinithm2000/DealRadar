from telegram.ext import Application
from app.bot.handlers import register_handlers
from app.services.scheduler import start_scheduler
from app.db.database import init_db
from app.utils.config import config
from app.utils.logger import logger
import sys

def main():
    """
    Main entry point for the Application
    """
    logger.info("Starting DealRadar Bot...")
    
    # 1. Initialize Database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize DB: {e}")
        sys.exit(1)
        
    # 2. Check for token
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        sys.exit(1)
        
    # 3. Build Bot
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # 4. Register Handlers
    register_handlers(app)
    
    # 5. Start Scheduler
    start_scheduler()
    
    # 6. Run Bot
    logger.info("Bot is polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
