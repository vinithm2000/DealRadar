from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .commands import (
    start, deals_command, topdeal, admin_stats, 
    fetch_deals, share_command, categories_command, 
    category_callback, cleardeals_command
)

def register_handlers(app: Application):
    """
    Registers all command and callback handlers with the application
    """
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deals", deals_command))
    app.add_handler(CommandHandler("topdeal", topdeal))
    app.add_handler(CommandHandler("admin", admin_stats))
    app.add_handler(CommandHandler("fetch", fetch_deals))
    app.add_handler(CommandHandler("share", share_command))
    app.add_handler(CommandHandler("categories", categories_command))
    app.add_handler(CommandHandler("cleardeals", cleardeals_command))
    
    # Callback handlers (for inline keyboard buttons)
    app.add_handler(CallbackQueryHandler(category_callback, pattern="^cat_"))
