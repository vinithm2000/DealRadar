from telegram.ext import Application, CommandHandler
from .commands import start, deals_command, topdeal, admin_stats, fetch_deals, share_command

def register_handlers(app: Application):
    """
    Registers all command handlers with the application
    """
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deals", deals_command))
    app.add_handler(CommandHandler("topdeal", topdeal))
    app.add_handler(CommandHandler("admin", admin_stats))
    app.add_handler(CommandHandler("fetch", fetch_deals))
    app.add_handler(CommandHandler("share", share_command))
