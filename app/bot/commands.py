from telegram import Update
from telegram.ext import ContextTypes
from app.db.database import get_latest_deals
from app.utils.logger import logger

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /start command
    """
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
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
