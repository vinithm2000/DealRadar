import asyncio
from urllib.parse import quote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.bot.formatting import build_deal_message
from app.bot.keyboards import (
    CATEGORY_EMOJIS,
    build_category_keyboard,
    build_deal_keyboard,
    build_platform_keyboard,
    build_settings_keyboard,
)
from app.db.database import (
    add_interaction,
    add_to_wishlist,
    clear_all_deals,
    clear_wishlist,
    create_manual_deal,
    ensure_user,
    get_deal_by_id,
    get_latest_deals,
    get_matching_users_for_deal,
    get_stats,
    get_todays_top_deals,
    get_user_categories,
    get_user_platforms,
    get_user_preferences,
    get_wishlist,
    mark_deal_inactive,
    save_user,
    search_deals,
    update_user_categories,
    update_user_platforms,
    update_user_settings,
)
from app.utils.config import config
from app.utils.logger import logger

AVAILABLE_CATEGORIES = [item[0] for item in [("electronics", ""), ("fashion", ""), ("food", ""), ("home", ""), ("bank_offers", ""), ("general", "")]]


def _is_admin(user_id):
    return not config.ADMIN_ID or str(user_id) == str(config.ADMIN_ID)


async def _send_deal(chat, deal):
    buy_url = deal.get("affiliate_url") or deal.get("url", "")
    await chat.reply_html(
        build_deal_message(deal),
        reply_markup=build_deal_keyboard(deal["id"], buy_url),
        disable_web_page_preview=False,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id)
    logger.info(f"User {user.id} started the bot")
    await update.message.reply_html(
        f"Welcome {user.mention_html()} to <b>DealRadar</b>.\n\n"
        "Pick the categories you want first. You can change these later with /settings or /categories.",
        reply_markup=build_category_keyboard(get_user_categories(user.id)),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "<b>DealRadar commands</b>\n\n"
        "/deals - Latest live deals\n"
        "/search <query> - Search active deals\n"
        "/wishlist - View saved deals\n"
        "/settings - Change categories, platforms, digest, quiet hours\n"
        "/todays - Top 5 deals from the last 24h\n"
        "/mute - Pause alerts\n"
        "/unmute - Resume alerts\n"
        "/categories - Quick category toggles\n"
        "/share - Share the bot"
    )


async def deals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    deals = get_latest_deals(limit=5)
    if not deals:
        await update.message.reply_text("No active deals yet. Run /fetch if you are testing as admin.")
        return
    for deal in deals:
        await _send_deal(update.message, deal)


async def todays_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deals = get_todays_top_deals(limit=5)
    if not deals:
        await update.message.reply_text("No top deals found for the last 24 hours.")
        return
    await update.message.reply_html("<b>Today's top deals</b>")
    for deal in deals:
        await _send_deal(update.message, deal)


async def topdeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deals = get_latest_deals(limit=1)
    if not deals:
        await update.message.reply_text("No top deal available yet.")
        return
    await _send_deal(update.message, deals[0])


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /search <keywords>")
        return
    results = search_deals(query, limit=3)
    if not results:
        await update.message.reply_text("No active deals matched that query.")
        return
    await update.message.reply_html(f"<b>Search results</b> for: <i>{query}</i>")
    for deal in results:
        await _send_deal(update.message, deal)


async def wishlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args and context.args[0].lower() == "clear":
        count = clear_wishlist(user_id)
        await update.message.reply_text(f"Cleared {count} saved deal(s).")
        return
    items = get_wishlist(user_id)
    if not items:
        await update.message.reply_text("Your wishlist is empty. Use the Save button on any deal.")
        return
    await update.message.reply_html(f"<b>Your wishlist</b> ({len(items)} saved)")
    for deal in items[:10]:
        await _send_deal(update.message, deal)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefs = get_user_preferences(update.effective_user.id)
    categories = ", ".join(cat.replace("_", " ").title() for cat in prefs["category_list"])
    platforms = ", ".join(platform.title() for platform in prefs["platform_list"])
    await update.message.reply_html(
        "<b>Settings</b>\n\n"
        f"Categories: {categories}\n"
        f"Platforms: {platforms}\n"
        f"Daily digest: {'On' if prefs['digest_on'] else 'Off'}\n"
        f"Quiet hours: {'On' if prefs['quiet_hours_on'] else 'Off'} "
        f"({prefs['quiet_start']:02d}:00-{prefs['quiet_end']:02d}:00)\n"
        f"Alerts: {'Muted' if prefs['muted'] else 'Live'}",
        reply_markup=build_settings_keyboard(prefs),
    )


async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_settings(update.effective_user.id, muted=1)
    await update.message.reply_text("Alerts muted. Use /unmute to resume.")


async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_settings(update.effective_user.id, muted=0)
    await update.message.reply_text("Alerts resumed.")


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    current = get_user_categories(user_id)
    await update.message.reply_html(
        "<b>Choose your categories</b>\nTap to toggle.",
        reply_markup=build_category_keyboard(current),
    )


async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not config.CHANNEL_ID:
        await update.message.reply_text("No public channel is configured.")
        return
    channel_name = config.CHANNEL_ID.replace("@", "")
    keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel_name}")]]
    await update.message.reply_html(
        f"Join the DealRadar channel: <b>{config.CHANNEL_ID}</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def bankoffers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deals = [deal for deal in get_latest_deals(limit=10) if deal.get("category") == "bank_offers"]
    if not deals:
        await update.message.reply_text("No bank card offers are active right now.")
        return
    for deal in deals[:5]:
        await _send_deal(update.message, deal)


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not _is_admin(user_id):
        await update.message.reply_text("Unauthorized.")
        return
    stats = get_stats()
    top_clicked = "\n".join(
        f"{index}. {item['title']} ({item['clicks']} buy clicks)"
        for index, item in enumerate(stats["top_clicked"], start=1)
    ) or "No click data yet."
    await update.message.reply_html(
        "<b>Bot stats</b>\n\n"
        f"Users: {stats['users']}\n"
        f"Active today: {stats['active_today']}\n"
        f"Active 7d: {stats['active_7d']}\n"
        f"Deals: {stats['total_deals']} total / {stats['active_deals']} active\n"
        f"Wishlist items: {stats['wishlist_count']}\n"
        f"Buy clicks: {stats['buy_clicks']}\n\n"
        f"<b>Top clicked deals</b>\n{top_clicked}"
    )


async def postdeal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not _is_admin(user_id):
        await update.message.reply_text("Unauthorized.")
        return
    payload = update.message.text.partition(" ")[2].strip()
    parts = [part.strip() for part in payload.split("|")]
    if len(parts) != 7:
        await update.message.reply_text(
            "Usage: /postdeal title | price | mrp | url | platform | category | hours_valid"
        )
        return
    deal = create_manual_deal(*parts)
    if not deal:
        await update.message.reply_text("Deal was not created. A matching URL may already exist.")
        return
    if config.CHANNEL_ID:
        try:
            await context.bot.send_message(
                chat_id=config.CHANNEL_ID,
                text=build_deal_message(deal),
                parse_mode="HTML",
                reply_markup=build_deal_keyboard(deal["id"], deal.get("affiliate_url") or deal["url"]),
                disable_web_page_preview=False,
            )
        except Exception as exc:
            logger.error(f"Channel postdeal broadcast failed: {exc}")
    for prefs in get_matching_users_for_deal(deal):
        try:
            await context.bot.send_message(
                chat_id=prefs["user_id"],
                text=build_deal_message(deal),
                parse_mode="HTML",
                reply_markup=build_deal_keyboard(deal["id"], deal.get("affiliate_url") or deal["url"]),
                disable_web_page_preview=False,
            )
        except Exception as exc:
            logger.error(f"User postdeal broadcast failed for {prefs['user_id']}: {exc}")
    await update.message.reply_html("<b>Deal posted</b>")
    await _send_deal(update.message, deal)


async def dealdone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not _is_admin(user_id):
        await update.message.reply_text("Unauthorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /dealdone <deal_id>")
        return
    changed = mark_deal_inactive(context.args[0].strip())
    await update.message.reply_text("Deal marked inactive." if changed else "Deal not found.")


async def fetch_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not _is_admin(user_id):
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text("Starting manual fetch. This can take 30-60 seconds.")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run_pipeline_sync)
        await update.message.reply_text(
            f"Fetched {result['raw_count']} raw deals.\n"
            f"Processed: {result['processed_count']}\n"
            f"Saved: {result['saved']}\n"
            f"Affiliate links: {result['affiliate_count']}\n"
            f"Total active deals: {result['active_deals']}"
        )
    except Exception as exc:
        logger.error(f"Fetch error: {exc}", exc_info=True)
        await update.message.reply_text(f"Fetch failed: {str(exc)[:250]}")


def _run_pipeline_sync():
    from app.core.processor import process_raw_deals
    from app.db.database import get_stats, purge_old_deals, save_deal
    from app.ingestion.aggregator import aggregate_all_sources
    from app.services.affiliate import generate_affiliate_link

    raw_deals = aggregate_all_sources()
    processed = process_raw_deals(raw_deals)
    purge_old_deals()

    saved = 0
    affiliate_count = 0
    for deal in processed:
        affiliate_url = generate_affiliate_link(deal["url"])
        deal["affiliate_url"] = affiliate_url
        if affiliate_url and affiliate_url != deal["url"]:
            affiliate_count += 1
        if save_deal(deal):
            saved += 1

    stats = get_stats()
    return {
        "raw_count": len(raw_deals),
        "processed_count": len(processed),
        "saved": saved,
        "affiliate_count": affiliate_count,
        "active_deals": stats["active_deals"],
    }


async def cleardeals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not _is_admin(user_id):
        await update.message.reply_text("Unauthorized.")
        return
    count = clear_all_deals()
    await update.message.reply_text(f"Cleared {count} deal(s) from the database.")


async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot.username
    share_text = quote("Check out DealRadar for live tech deals.")
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text={share_text}"
    keyboard = [[InlineKeyboardButton("Share DealRadar", url=share_url)]]
    await update.message.reply_text("Share DealRadar with friends.", reply_markup=InlineKeyboardMarkup(keyboard))


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    ensure_user(user_id)
    selected = query.data.replace("cat_", "")
    current = get_user_categories(user_id)
    if selected == "all":
        new_cats = ["all"] if "all" not in current else ["electronics"]
    else:
        if "all" in current:
            current = []
        if selected in current:
            current.remove(selected)
        else:
            current.append(selected)
        new_cats = current or ["all"]
    update_user_categories(user_id, ",".join(new_cats))
    await query.answer("Categories updated.")
    await query.edit_message_text(
        "Choose your categories.",
        reply_markup=build_category_keyboard(new_cats),
    )


async def platform_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    current = get_user_platforms(user_id)
    selected = query.data.replace("platform_", "")
    if selected == "all":
        new_platforms = ["all"] if "all" not in current else ["amazon"]
    else:
        if "all" in current:
            current = []
        if selected in current:
            current.remove(selected)
        else:
            current.append(selected)
        new_platforms = current or ["all"]
    update_user_platforms(user_id, ",".join(new_platforms))
    await query.answer("Platforms updated.")
    await query.edit_message_text(
        "Choose the platforms you want.",
        reply_markup=build_platform_keyboard(new_platforms),
    )


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    prefs = get_user_preferences(user_id)
    action = query.data

    if action == "settings_digest":
        update_user_settings(user_id, digest_on=0 if prefs["digest_on"] else 1)
    elif action == "settings_mute":
        update_user_settings(user_id, muted=0 if prefs["muted"] else 1)
    elif action == "settings_quiet_toggle":
        update_user_settings(user_id, quiet_hours_on=0 if prefs["quiet_hours_on"] else 1)
    elif action == "settings_quiet_window":
        next_start = (prefs["quiet_start"] + 1) % 24
        next_end = (prefs["quiet_end"] + 1) % 24
        update_user_settings(user_id, quiet_start=next_start, quiet_end=next_end, quiet_hours_on=1)
    elif action == "settings_categories":
        await query.answer()
        await query.edit_message_text("Choose your categories.", reply_markup=build_category_keyboard(get_user_categories(user_id)))
        return
    elif action == "settings_platforms":
        await query.answer()
        await query.edit_message_text("Choose the platforms you want.", reply_markup=build_platform_keyboard(get_user_platforms(user_id)))
        return

    prefs = get_user_preferences(user_id)
    await query.answer("Settings updated.")
    await query.edit_message_text(
        "Your settings were updated.",
        reply_markup=build_settings_keyboard(prefs),
    )


async def onboarding_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    update_user_settings(user_id, onboarding_done=1)
    await query.answer("Saved.")
    await query.edit_message_text(
        "Setup saved. Use /deals, /search, /wishlist, or /settings any time."
    )


async def deal_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    parts = query.data.split("_")
    verb = parts[0]
    deal_id = "_".join(parts[1:]) if verb == "save" else "_".join(parts[2:])
    if verb == "save":
        ok, message = add_to_wishlist(user_id, deal_id)
        if ok:
            add_interaction(user_id, deal_id, "save")
        await query.answer(message, show_alert=not ok)
        return
    if verb == "share":
        deal = get_deal_by_id(deal_id)
        if not deal:
            await query.answer("Deal not found.", show_alert=True)
            return
        share_text = quote(f"{deal['title']} - {deal.get('affiliate_url') or deal.get('url')}")
        keyboard = [[InlineKeyboardButton("Share this deal", url=f"https://t.me/share/url?url=&text={share_text}")]]
        await query.answer()
        await query.message.reply_text("Share this deal:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if verb == "react":
        action = parts[1]
        if add_interaction(user_id, deal_id, action):
            if action == "expired":
                mark_deal_inactive(deal_id)
            await query.answer("Feedback saved.")
        else:
            await query.answer("Already recorded.")
