from telegram.ext import Application, CommandHandler
from .commands import start, deals_command, topdeal

def register_handlers(app: Application):
    """
    Registers all command handlers with the application
    """
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deals", deals_command))
    app.add_handler(CommandHandler("topdeal", topdeal))
