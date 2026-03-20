from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.db.database import get_latest_deals
from app.utils.logger import logger

AVAILABLE_CATEGORIES = ['electronics', 'fashion', 'food', 'home', 'general']
CATEGORY_EMOJIS = {
    'electronics': '📱', 'fashion': '👗', 'food': '🍔', 
    'home': '🏠', 'general': '📦', 'all': '🌐'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command"""
    from app.db.database import save_user
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    save_user(user.id)
    
    await update.message.reply_html(
        f"Hi {user.mention_html()}! Welcome to <b>DealRadar</b> 🎯\n\n"
        f"I'll send you the best deals automatically — no need to ask!\n\n"
        f"📱 /deals — See top deals now\n"
        f"🏆 /topdeal — Best deal today\n"
        f"📂 /categories — Choose what deals you want\n"
        f"📱 /share — Invite friends\n\n"
        f"💡 <i>Tip: Use /categories to only get deals you care about!</i>"
    )

async def deals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /deals command - sends top 5 deals"""
    logger.info(f"User {update.effective_user.id} requested latest deals")
    deals = get_latest_deals(limit=5)
    
    if not deals:
        await update.message.reply_text("No deals found yet. Check back later!")
        return

    for d in deals:
        buy_url = d.get('affiliate_url') or d.get('url', '')
        cat_emoji = CATEGORY_EMOJIS.get(d.get('category', 'general'), '📦')
        
        message = (
            f"🔥 <b>{d['title']}</b>\n\n"
            f"⭐ Score: {d['score']}\n"
            f"{cat_emoji} {d.get('category', 'general').capitalize()}\n\n"
            f"🛒 <a href='{buy_url}'>BUY NOW →</a>"
        )
        
        keyboard = [[InlineKeyboardButton("🛒 Buy Now", url=buy_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(message, reply_markup=reply_markup)

async def topdeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /topdeal command - sends the best deal"""
    deals = get_latest_deals(limit=1)
    if not deals:
        await update.message.reply_text("No top deal available yet.")
        return
        
    d = deals[0]
    buy_url = d.get('affiliate_url') or d.get('url', '')
    
    message = (
        f"🏆 <b>BEST DEAL TODAY</b>\n\n"
        f"🔥 {d['title']}\n"
        f"⭐ Quality Score: {d['score']}\n\n"
        f"🛒 <a href='{buy_url}'>BUY NOW →</a>"
    )
    
    keyboard = [[InlineKeyboardButton("🛒 Buy Now", url=buy_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(message, reply_markup=reply_markup)

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /categories command - lets users pick deal categories"""
    from app.db.database import get_user_categories
    
    user_id = update.effective_user.id
    current_cats = get_user_categories(user_id)
    
    # Build inline keyboard
    buttons = []
    
    # "All" button
    all_check = "✅" if 'all' in current_cats else "⬜"
    buttons.append([InlineKeyboardButton(f"{all_check} 🌐 All Deals", callback_data="cat_all")])
    
    # Category buttons (2 per row)
    row = []
    for cat in AVAILABLE_CATEGORIES:
        emoji = CATEGORY_EMOJIS.get(cat, '📦')
        check = "✅" if cat in current_cats else "⬜"
        row.append(InlineKeyboardButton(f"{check} {emoji} {cat.capitalize()}", callback_data=f"cat_{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await update.message.reply_text(
        "📂 <b>Choose your deal categories</b>\n\n"
        "Tap to toggle. You'll only receive deals matching your selections.\n"
        "Choose 'All Deals' to get everything.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles category button presses"""
    from app.db.database import get_user_categories, update_user_categories
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    selected = query.data.replace("cat_", "")
    
    current_cats = get_user_categories(user_id)
    
    if selected == "all":
        # Toggle "all"
        if 'all' in current_cats:
            new_cats = ['electronics']  # Default if deselecting all
        else:
            new_cats = ['all']
    else:
        # Remove "all" if it was selected
        if 'all' in current_cats:
            current_cats = []
        
        # Toggle the selected category
        if selected in current_cats:
            current_cats.remove(selected)
        else:
            current_cats.append(selected)
        
        new_cats = current_cats if current_cats else ['all']
    
    update_user_categories(user_id, ','.join(new_cats))
    
    # Rebuild keyboard with updated state
    buttons = []
    all_check = "✅" if 'all' in new_cats else "⬜"
    buttons.append([InlineKeyboardButton(f"{all_check} 🌐 All Deals", callback_data="cat_all")])
    
    row = []
    for cat in AVAILABLE_CATEGORIES:
        emoji = CATEGORY_EMOJIS.get(cat, '📦')
        check = "✅" if cat in new_cats else "⬜"
        row.append(InlineKeyboardButton(f"{check} {emoji} {cat.capitalize()}", callback_data=f"cat_{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(
        f"📂 <b>Choose your deal categories</b>\n\n"
        f"Tap to toggle. Current: <b>{', '.join(c.capitalize() for c in new_cats)}</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /admin command"""
    from app.utils.config import config
    from app.db.database import get_stats
    
    user_id = update.effective_user.id
    if config.ADMIN_ID and str(user_id) != str(config.ADMIN_ID):
        await update.message.reply_text("Unauthorized.")
        return
        
    stats = get_stats()
    message = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: {stats['users']}\n"
        f"📦 Total Deals: {stats['total_deals']}\n"
        f"🆕 Recent (48h): {stats['recent_deals']}\n"
        f"✅ Posted Deals: {stats['posted_deals']}\n"
    )
    await update.message.reply_html(message)

async def fetch_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /fetch command - manually triggers the pipeline (Admin only)"""
    from app.utils.config import config
    from app.services.scheduler import run_deal_pipeline
    
    user_id = update.effective_user.id
    if config.ADMIN_ID and str(user_id) != str(config.ADMIN_ID):
        await update.message.reply_text("Unauthorized.")
        return
        
    await update.message.reply_text("⚡ Starting manual deal fetch... please wait.")
    
    from app.db.database import purge_old_deals
    purge_old_deals()
    
    run_deal_pipeline() 
    
    from app.db.database import get_stats
    stats = get_stats()
    await update.message.reply_text(
        f"✅ Fetch completed!\n"
        f"🆕 Recent deals in DB: {stats['recent_deals']}\n"
        f"Use /deals to see top picks."
    )

async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /share command - helps users invite others"""
    bot_username = context.bot.username
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text=Check out DealRadar — best tech deals in India, delivered to you automatically! 🚀🔥"
    
    keyboard = [[InlineKeyboardButton("📱 Share with Friends", url=share_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Love using DealRadar? Share it with your friends and help them save money too! 💰",
        reply_markup=reply_markup
    )
