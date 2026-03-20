from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.ingestion.aggregator import aggregate_all_sources
from app.core.processor import process_raw_deals
from app.db.database import save_deal, purge_old_deals
from app.services.affiliate import generate_affiliate_link
from app.utils.config import config
from app.utils.logger import logger
import datetime

def run_deal_pipeline(app=None):
    """
    Orchestrates the entire fetching and processing flow
    """
    try:
        logger.info("Pipeline: Starting scheduled job")
        
        # Purge old deals first
        purge_old_deals()
        
        # 1. Ingest
        raw_deals = aggregate_all_sources()
        
        # 2. Process (Filter + Dedup + Score)
        processed_deals = process_raw_deals(raw_deals)
        
        # 3. Enrich & Save
        saved_count = 0
        for d in processed_deals:
            d['affiliate_url'] = generate_affiliate_link(d['url'])
            if save_deal(d):
                saved_count += 1
            
        logger.info(f"Pipeline: Saved {saved_count} new deals to DB (out of {len(processed_deals)} processed)")
        
        # 4. Broadcast new deals to subscribers (if app is provided)
        if app and saved_count > 0:
            import asyncio
            from .notifier import broadcast_new_deals
            
            try:
                loop = app.loop
            except AttributeError:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    
            asyncio.run_coroutine_threadsafe(broadcast_new_deals(app), loop)
        elif saved_count == 0:
            logger.info("Pipeline: No new deals to broadcast")

    except Exception as e:
        logger.error(f"Pipeline: Error during execution: {e}", exc_info=True)

def start_scheduler(app):
    """
    Initializes and starts the background scheduler.
    Runs first job immediately, then every N minutes.
    """
    interval = config.SCHEDULE_INTERVAL_MIN
    scheduler = BackgroundScheduler()
    
    # Schedule recurring job
    scheduler.add_job(
        run_deal_pipeline, 
        IntervalTrigger(minutes=interval),
        args=[app], 
        id='deal_pipeline',
        name='Deal Pipeline',
        next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=30)  # First run 30s after startup
    )
    
    scheduler.start()
    logger.info(f"Scheduler started (interval: {interval} min, first run in 30s)")
    return scheduler
