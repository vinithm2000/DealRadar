from telegram.ext import Application
from app.db.database import get_all_users, get_latest_deals, mark_deal_as_posted
from app.utils.logger import logger

async def broadcast_new_deals(app: Application):
    """
    Broadcasts new, unposted deals to all registered users
    """
    logger.info("Broadcaster: Checking for new deals to broadcast")
    
    # Get top 3 unposted deals
    deals = get_latest_deals(limit=3, only_unposted=True)
    if not deals:
        logger.info("Broadcaster: No new deals to broadcast")
        return
        
    users = get_all_users()
    if not users:
        logger.info("Broadcaster: No users to notify")
        return
        
    logger.info(f"Broadcaster: Notifying {len(users)} users about {len(deals)} deals")
    
    for d in deals:
        message = (
            f"🚀 <b>NEW HOT DEAL!</b>\n\n"
            f"🔥 {d['title']}\n"
            f"💰 Score: {d['score']}\n\n"
            f"🛒 BUY NOW: {d['affiliate_url'] or d['url']}"
        )
        
        for user_id in users:
            try:
                await app.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Broadcaster: Failed to send to {user_id}: {e}")
                
        # Mark as posted
        mark_deal_as_posted(d['id'])
