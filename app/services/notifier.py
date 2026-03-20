import asyncio
from telegram.ext import Application
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.db.database import get_users_by_category, get_latest_deals, mark_deal_as_posted, get_all_users
from app.utils.logger import logger

async def broadcast_new_deals(app: Application):
    """
    Broadcasts new, unposted deals to subscribers based on their category preferences.
    Rate-limited to avoid Telegram flood limits.
    """
    logger.info("Broadcaster: Checking for new deals to broadcast")
    
    # Get top 5 unposted deals
    deals = get_latest_deals(limit=5, only_unposted=True)
    if not deals:
        logger.info("Broadcaster: No new deals to broadcast")
        return
    
    total_sent = 0
    
    for d in deals:
        category = d.get('category', 'general')
        
        # Get users subscribed to this deal's category
        users = get_users_by_category(category)
        if not users:
            logger.info(f"Broadcaster: No users subscribed to '{category}'")
            mark_deal_as_posted(d['id'])
            continue
        
        # Build rich message with Buy Now button
        buy_url = d.get('affiliate_url') or d.get('url', '')
        
        message = (
            f"🚀 <b>NEW DEAL!</b>\n\n"
            f"🔥 {d['title']}\n\n"
            f"⭐ Score: {d['score']}\n"
            f"📂 Category: {category.capitalize()}\n\n"
            f"🛒 <a href='{buy_url}'>BUY NOW →</a>"
        )
        
        # Inline button for easy access
        keyboard = [[InlineKeyboardButton("🛒 Buy Now", url=buy_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        for user_id in users:
            try:
                await app.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
                total_sent += 1
                
                # Rate limit: 1 message per second to avoid Telegram flood
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Broadcaster: Failed to send to {user_id}: {e}")
                
        # Mark as posted after sending to all users
        mark_deal_as_posted(d['id'])
    
    logger.info(f"Broadcaster: Sent {total_sent} messages for {len(deals)} deals")
