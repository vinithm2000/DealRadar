"""
Deal pipeline scheduler using telegram's JobQueue.
"""

import asyncio

from app.bot.formatting import build_deal_message
from app.bot.keyboards import build_deal_keyboard
from app.db.database import (
    expire_deals,
    get_latest_deals,
    get_matching_users_for_deal,
    get_todays_top_deals,
    get_user_preferences,
    mark_deal_as_posted,
    purge_old_deals,
    save_deal,
)
from app.utils.config import config
from app.utils.logger import logger


async def scheduled_pipeline(context):
    try:
        logger.info("Pipeline: starting scheduled job")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run_pipeline_sync)
        expire_deals()
        if result["saved"] > 0:
            await _broadcast_to_channel(context)
            await _broadcast_to_subscribers(context)
        logger.info(f"Pipeline: complete with {result['saved']} new deals")
    except Exception as exc:
        logger.error(f"Pipeline: error: {exc}", exc_info=True)


def _run_pipeline_sync():
    from app.core.processor import process_raw_deals
    from app.ingestion.aggregator import aggregate_all_sources
    from app.services.affiliate import generate_affiliate_link

    purge_old_deals()
    raw_deals = aggregate_all_sources()
    processed = process_raw_deals(raw_deals)
    saved = 0
    affiliate_count = 0
    for deal in processed:
        deal["affiliate_url"] = generate_affiliate_link(deal["url"])
        if deal["affiliate_url"] and deal["affiliate_url"] != deal["url"]:
            affiliate_count += 1
        if save_deal(deal):
            saved += 1
    return {"saved": saved, "affiliate_count": affiliate_count}


async def send_deal_message(bot, chat_id, deal):
    buy_url = deal.get("affiliate_url") or deal.get("url", "")
    await bot.send_message(
        chat_id=chat_id,
        text=build_deal_message(deal),
        parse_mode="HTML",
        reply_markup=build_deal_keyboard(deal["id"], buy_url),
        disable_web_page_preview=False,
    )


async def _broadcast_to_channel(context):
    if not config.CHANNEL_ID:
        return
    deals = get_latest_deals(limit=5, only_unposted=True)
    for deal in deals:
        try:
            await send_deal_message(context.bot, config.CHANNEL_ID, deal)
            await asyncio.sleep(1)
        except Exception as exc:
            logger.error(f"Channel broadcast error: {exc}")


async def _broadcast_to_subscribers(context):
    deals = get_latest_deals(limit=5, only_unposted=True)
    for deal in deals:
        recipients = get_matching_users_for_deal(deal)
        for prefs in recipients:
            try:
                await send_deal_message(context.bot, prefs["user_id"], deal)
                await asyncio.sleep(0.2)
            except Exception as exc:
                logger.error(f"User broadcast failed for {prefs['user_id']}: {exc}")
        mark_deal_as_posted(deal["id"])


async def daily_digest_job(context):
    deals = get_todays_top_deals(limit=5)
    if not deals:
        return
    from app.db.database import get_all_users

    for user_id in get_all_users():
        prefs = get_user_preferences(user_id)
        if not prefs.get("digest_on") or prefs.get("muted"):
            continue
        lines = ["<b>Today's top deals</b>", ""]
        for deal in deals:
            lines.append(build_deal_message(deal, compact=True))
            lines.append("")
        try:
            await context.bot.send_message(chat_id=user_id, text="\n".join(lines).strip(), parse_mode="HTML")
            await asyncio.sleep(0.2)
        except Exception as exc:
            logger.error(f"Digest send failed for {user_id}: {exc}")


async def expiry_job(context):
    expire_deals()


def setup_scheduler(app):
    interval = config.SCHEDULE_INTERVAL_MIN * 60
    app.job_queue.run_repeating(scheduled_pipeline, interval=interval, first=30, name="deal_pipeline")
    app.job_queue.run_daily(daily_digest_job, time=__import__("datetime").time(hour=9, minute=0), name="daily_digest")
    app.job_queue.run_repeating(expiry_job, interval=1800, first=60, name="expiry_job")
    logger.info(f"Scheduler: configured pipeline every {config.SCHEDULE_INTERVAL_MIN} min, digest at 09:00")

