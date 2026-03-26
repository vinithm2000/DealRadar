from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from .commands import (
    admin_stats,
    bankoffers_command,
    categories_command,
    category_callback,
    channel_command,
    cleardeals_command,
    deal_action_callback,
    dealdone_command,
    deals_command,
    fetch_deals,
    help_command,
    mute_command,
    onboarding_done_callback,
    platform_callback,
    postdeal_command,
    search_command,
    settings_callback,
    settings_command,
    share_command,
    start,
    todays_command,
    topdeal,
    unmute_command,
    wishlist_command,
)


def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("deals", deals_command))
    app.add_handler(CommandHandler("todays", todays_command))
    app.add_handler(CommandHandler("topdeal", topdeal))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("wishlist", wishlist_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("categories", categories_command))
    app.add_handler(CommandHandler("share", share_command))
    app.add_handler(CommandHandler("channel", channel_command))
    app.add_handler(CommandHandler("bankoffers", bankoffers_command))

    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("admin", admin_stats))
    app.add_handler(CommandHandler("fetch", fetch_deals))
    app.add_handler(CommandHandler("cleardeals", cleardeals_command))
    app.add_handler(CommandHandler("postdeal", postdeal_command))
    app.add_handler(CommandHandler("dealdone", dealdone_command))

    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat_"))
    app.add_handler(CallbackQueryHandler(platform_callback, pattern=r"^platform_"))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^settings_"))
    app.add_handler(CallbackQueryHandler(onboarding_done_callback, pattern=r"^onboard_done$"))
    app.add_handler(CallbackQueryHandler(deal_action_callback, pattern=r"^(save_|share_|react_)"))

