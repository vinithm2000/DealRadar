from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.db.database import get_latest_deals
from app.utils.logger import logger

AVAILABLE_CATEGORIES = ['electronics', 'fashion', 'food', 'home', 'general']
CATEGORY_EMOJIS = {
    'electronics': '📱', 'fashion': '👗', 'food': '🍔', 
    'home': '🏠', 'general': '📦', 'all': '🌐'
}

def _build_category_keyboard(current_cats):
    """Build an inline keyboard for category selection"""
    buttons = []
    
    all_check = "✅" if 'all' in current_cats else "⬜"
    buttons.append([InlineKeyboardButton(f"{all_check} 🌐 All Deals", callback_data="cat_all")])
    
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
    
    return InlineKeyboardMarkup(buttons)

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
    from app.db.database import get_user_categories, save_user
    
    user_id = update.effective_user.id
    # Ensure user exists in DB
    save_user(user_id)
    
    current_cats = get_user_categories(user_id)
    reply_markup = _build_category_keyboard(current_cats)
    
    cats_display = ', '.join(c.capitalize() for c in current_cats)
    
    await update.message.reply_text(
        f"📂 <b>Choose your deal categories</b>\n\n"
        f"Tap to toggle. Current: <b>{cats_display}</b>\n"
        f"Choose 'All Deals' to get everything.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles category button presses"""
    from app.db.database import get_user_categories, update_user_categories, save_user
    
    query = update.callback_query
    
    try:
        user_id = query.from_user.id
        selected = query.data.replace("cat_", "")
        
        # Ensure user exists
        save_user(user_id)
        
        current_cats = get_user_categories(user_id)
        logger.info(f"Category toggle: user={user_id}, selected={selected}, current={current_cats}")
        
        if selected == "all":
            if 'all' in current_cats:
                new_cats = ['electronics']
            else:
                new_cats = ['all']
        else:
            # Remove "all" if switching to specific
            if 'all' in current_cats:
                current_cats = []
            
            # Toggle
            if selected in current_cats:
                current_cats.remove(selected)
            else:
                current_cats.append(selected)
            
            new_cats = current_cats if current_cats else ['all']
        
        update_user_categories(user_id, ','.join(new_cats))
        cats_display = ', '.join(c.capitalize() for c in new_cats)
        logger.info(f"Category updated: user={user_id}, new_cats={new_cats}")
        
        # Show popup toast so user knows it worked
        await query.answer(text=f"✅ Updated to: {cats_display}", show_alert=False)
        
        # Rebuild keyboard with updated checkmarks
        reply_markup = _build_category_keyboard(new_cats)
        
        # Build list of selected categories with emojis
        selected_display = ""
        for c in new_cats:
            emoji = CATEGORY_EMOJIS.get(c, '📦')
            selected_display += f"\n   {emoji} {c.capitalize()}"
        
        await query.edit_message_text(
            f"📂 <b>Your Deal Preferences</b>\n\n"
            f"🔔 You'll receive:{selected_display}\n\n"
            f"Tap buttons below to change:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Category callback error: {e}", exc_info=True)
        try:
            await query.answer(text=f"❌ Error: {str(e)[:100]}", show_alert=True)
        except:
            pass

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
    """Handles /fetch command - manually triggers the pipeline with diagnostics"""
    from app.utils.config import config
    import asyncio
    import concurrent.futures
    
    user_id = update.effective_user.id
    if config.ADMIN_ID and str(user_id) != str(config.ADMIN_ID):
        await update.message.reply_text("Unauthorized.")
        return
        
    await update.message.reply_text("⚡ Starting manual deal fetch... please wait (30-60 seconds).")
    
    try:
        # Run the blocking pipeline in a thread executor to avoid asyncio conflicts
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run_pipeline_sync)
        
        # Send results
        await update.message.reply_text(
            f"📡 Fetched {result['raw_count']} raw deals:\n{result['source_info']}"
        )
        
        await update.message.reply_text(
            f"✅ Fetch completed!\n\n"
            f"📊 Results:\n"
            f"  • Raw deals: {result['raw_count']}\n"
            f"  • After filters: {result['processed_count']}\n"
            f"  • New saved: {result['saved']}\n"
            f"  • With EarnKaro: {result['affiliate_count']}\n"
            f"  • Total in DB: {result['total_in_db']}\n\n"
            f"🔗 Sample deals:{result['sample']}"
        )
    except Exception as e:
        logger.error(f"Fetch error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Fetch error: {str(e)[:300]}")

def _run_pipeline_sync():
    """
    Runs the deal pipeline synchronously (called from thread executor).
    Returns a dict with diagnostic results.
    """
    from app.ingestion.aggregator import aggregate_all_sources
    from app.core.processor import process_raw_deals
    from app.db.database import save_deal, purge_old_deals, get_stats
    from app.services.affiliate import generate_affiliate_link
    
    # Step 1: Ingest
    raw_deals = aggregate_all_sources()
    
    source_counts = {}
    for d in raw_deals:
        src = d.get('source', 'unknown')
        source_counts[src] = source_counts.get(src, 0) + 1
    
    source_info = "\n".join(f"  • {k}: {v}" for k, v in sorted(source_counts.items()))
    
    # Step 2: Process
    processed = process_raw_deals(raw_deals)
    
    # Step 3: Save with affiliate links
    purge_old_deals()
    
    saved = 0
    affiliate_count = 0
    for d in processed:
        aff_url = generate_affiliate_link(d['url'])
        d['affiliate_url'] = aff_url
        if aff_url and aff_url != d['url']:
            affiliate_count += 1
        if save_deal(d):
            saved += 1
    
    stats = get_stats()
    
    # Show top 3 deal URLs for debugging
    sample = ""
    for d in processed[:3]:
        aff = "✅ EarnKaro" if d.get('affiliate_url') and d['affiliate_url'] != d['url'] else "❌ No affiliate"
        sample += f"\n• [{d['source']}] {aff}\n  {d['url'][:60]}..."
    
    return {
        'raw_count': len(raw_deals),
        'source_info': source_info,
        'processed_count': len(processed),
        'saved': saved,
        'affiliate_count': affiliate_count,
        'total_in_db': stats['recent_deals'],
        'sample': sample,
    }


async def cleardeals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /cleardeals command - clears ALL deals from DB (Admin only)"""
    from app.utils.config import config
    from app.db.database import clear_all_deals
    
    user_id = update.effective_user.id
    if config.ADMIN_ID and str(user_id) != str(config.ADMIN_ID):
        await update.message.reply_text("Unauthorized.")
        return
    
    count = clear_all_deals()
    await update.message.reply_text(f"🗑️ Cleared {count} deals from database. Run /fetch to get fresh ones.")

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
