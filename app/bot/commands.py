from telegram import Update
from telegram.ext import ContextTypes
from app.db.database import get_latest_deals
from app.utils.logger import logger

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /start command
    """
    from app.db.database import save_user
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Save user to DB
    save_user(user.id)
    
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Welcome to DealRadar. "
        f"I'll help you find the best tech deals in India. "
        f"\n\nUse /deals to see latest verified offers."
    )

async def deals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /deals command - sends top 5 deals
    """
    logger.info(f"User {update.effective_user.id} requested latest deals")
    deals = get_latest_deals(limit=5)
    
    if not deals:
        await update.message.reply_text("No deals found yet. Check back later!")
        return

    for d in deals:
        message = (
            f"🔥 <b>{d['title']}</b>\n\n"
            f"⭐ Score: {d['score']}\n"
            f"🛒 BUY NOW: {d['affiliate_url'] or d['url']}\n"
        )
        await update.message.reply_html(message)

async def topdeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /topdeal command - sends the best deal
    """
    deals = get_latest_deals(limit=1)
    if not deals:
        await update.message.reply_text("No top deal available yet.")
        return
        
    d = deals[0]
    message = (
        f"🏆 <b>BEST DEAL TODAY</b>\n\n"
        f"🔥 {d['title']}\n"
        f"⭐ Quality Score: {d['score']}\n\n"
        f"🛒 BUY NOW: {d['affiliate_url'] or d['url']}"
    )
    await update.message.reply_html(message)
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /admin command
    """
    from app.utils.config import config
    from app.db.database import get_stats
    
    user_id = update.effective_user.id
    if config.ADMIN_ID and str(user_id) != str(config.ADMIN_ID):
        await update.message.reply_text("Unauthorized. This command is for administrators only.")
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
    """
    Handles /fetch command - manually triggers the pipeline (Admin only)
    """
    from app.utils.config import config
    from app.services.scheduler import run_deal_pipeline
    
    user_id = update.effective_user.id
    if config.ADMIN_ID and str(user_id) != str(config.ADMIN_ID):
        await update.message.reply_text("Unauthorized.")
        return
        
    await update.message.reply_text("⚡ Starting manual deal fetch... please wait.")
    
    # Purge old deals first
    from app.db.database import purge_old_deals
    purge_old_deals()
    
    # Run pipeline
    run_deal_pipeline() 
    
    from app.db.database import get_stats
    stats = get_stats()
    await update.message.reply_text(
        f"✅ Fetch completed!\n"
        f"🆕 Recent deals in DB: {stats['recent_deals']}\n"
        f"Use /deals to see top picks."
    )

async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /share command - helps users invite others
    """
    bot_username = context.bot.username
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text=Check out this amazing Deals Bot for tech offers in India! 🚀"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton("📱 Share with Friends", url=share_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Love using DealRadar? Share it with your friends and help them save money too! 💰",
        reply_markup=reply_markup
    )
