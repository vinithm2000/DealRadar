from apscheduler.schedulers.background import BackgroundScheduler
from app.ingestion.aggregator import aggregate_all_sources
from app.core.processor import process_raw_deals
from app.db.database import save_deal
from app.services.affiliate import generate_affiliate_link
from app.utils.logger import logger

def run_deal_pipeline():
    """
    Orchestrates the entire fetching and processing flow
    """
    try:
        logger.info("Pipeline: Starting scheduled job")
        
        # 1. Ingest
        raw_deals = aggregate_all_sources()
        
        # 2. Process (Filter + Dedup + Score)
        processed_deals = process_raw_deals(raw_deals)
        
        # 3. Enrich & Save
        for d in processed_deals:
            d['affiliate_url'] = generate_affiliate_link(d['url'])
            save_deal(d)
            
        logger.info(f"Pipeline: Successfully saved {len(processed_deals)} deals to DB")
    except Exception as e:
        logger.error(f"Pipeline: Error during execution: {e}")

def start_scheduler():
    """
    Initializes and starts the background scheduler
    """
    scheduler = BackgroundScheduler()
    # Run pipeline every 30 minutes
    scheduler.add_job(run_deal_pipeline, "interval", minutes=30, next_run_time=None)
    scheduler.start()
    logger.info("Scheduler started (interval: 30 minutes)")
    return scheduler
