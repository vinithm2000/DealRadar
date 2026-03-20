from telegram.ext import Application
from telegram import Update
from app.bot.handlers import register_handlers
from app.services.scheduler import start_scheduler
from app.db.database import init_db
from app.utils.config import config
from app.utils.logger import logger
import sys
import traceback

async def error_handler(update: object, context):
    """Global error handler - logs errors and notifies the user"""
    logger.error(f"Exception: {context.error}", exc_info=context.error)
    
    # Try to notify the user
    if isinstance(update, Update) and update.effective_message:
        try:
            error_msg = str(context.error)[:200]
            await update.effective_message.reply_text(
                f"⚠️ An error occurred: {error_msg}\n\nPlease try again."
            )
        except:
            pass
    
    # If it's a callback query, try to answer it
    if isinstance(update, Update) and update.callback_query:
        try:
            await update.callback_query.answer(
                text="Error occurred. Try /categories again.", 
                show_alert=True
            )
        except:
            pass

def main():
    """
    Main entry point for the Application
    """
    logger.info("Starting DealRadar Bot...")
    
    # 1. Initialize Database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize DB: {e}")
        traceback.print_exc()
        sys.exit(1)
        
    # 2. Check for token
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        sys.exit(1)
        
    # 3. Build Bot
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # 4. Register Handlers
    register_handlers(app)
    
    # 5. Add error handler
    app.add_error_handler(error_handler)
    
    # 6. Start Scheduler
    start_scheduler(app)
    
    # 7. Run Bot
    logger.info("Bot is polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
