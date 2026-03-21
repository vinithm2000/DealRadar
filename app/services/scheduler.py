from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.ingestion.aggregator import aggregate_all_sources
from app.core.processor import process_raw_deals
from app.db.database import save_deal, purge_old_deals
from app.services.affiliate import generate_affiliate_link
from app.utils.config import config
from app.utils.logger import logger
import asyncio
import datetime
import threading

# Store reference to the bot app globally
_bot_app = None

def run_deal_pipeline(app=None):
    """
    Orchestrates the entire fetching and processing flow.
    Called by APScheduler from a background thread.
    """
    global _bot_app
    if app:
        _bot_app = app
    
    try:
        logger.info("=" * 50)
        logger.info("Pipeline: Starting scheduled job")
        
        # Purge old deals first
        purge_old_deals()
        
        # 1. Ingest from all sources
        raw_deals = aggregate_all_sources()
        logger.info(f"Pipeline: Got {len(raw_deals)} raw deals from all sources")
        
        if not raw_deals:
            logger.warning("Pipeline: No raw deals fetched from any source!")
            return
        
        # 2. Process (Filter + Dedup + Score)
        processed_deals = process_raw_deals(raw_deals)
        logger.info(f"Pipeline: {len(processed_deals)} deals after processing")
        
        if not processed_deals:
            logger.warning("Pipeline: No deals passed filters!")
            return
        
        # 3. Enrich with affiliate links & Save
        saved_count = 0
        for d in processed_deals:
            d['affiliate_url'] = generate_affiliate_link(d['url'])
            if save_deal(d):
                saved_count += 1
            
        logger.info(f"Pipeline: Saved {saved_count} NEW deals (out of {len(processed_deals)} processed)")
        
        # 4. Broadcast new deals to subscribers
        if _bot_app and saved_count > 0:
            _broadcast_deals(_bot_app)
        elif saved_count == 0:
            logger.info("Pipeline: No new deals to broadcast (all duplicates)")
        
        logger.info("Pipeline: Job complete")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Pipeline: Error during execution: {e}", exc_info=True)

def _broadcast_deals(app):
    """
    Broadcast new deals. Handles the async/thread boundary properly.
    APScheduler runs in a background thread, but Telegram bot runs in asyncio.
    """
    from .notifier import broadcast_new_deals
    
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(broadcast_new_deals(app))
            logger.info("Pipeline: Broadcasting completed successfully")
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Pipeline: Broadcasting error: {e}", exc_info=True)

def start_scheduler(app):
    """
    Initializes and starts the background scheduler.
    Runs first job 30s after startup, then every N minutes.
    """
    global _bot_app
    _bot_app = app
    
    interval = config.SCHEDULE_INTERVAL_MIN
    scheduler = BackgroundScheduler()
    
    # Schedule recurring job
    scheduler.add_job(
        run_deal_pipeline, 
        IntervalTrigger(minutes=interval),
        args=[app], 
        id='deal_pipeline',
        name='Deal Pipeline',
        next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=30)
    )
    
    scheduler.start()
    logger.info(f"Scheduler started (interval: {interval} min, first run in 30s)")
    return scheduler
