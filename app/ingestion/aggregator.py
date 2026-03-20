from .reddit import fetch_reddit_deals
from .rss import fetch_rss_deals
from app.utils.logger import logger

def aggregate_all_sources():
    """
    Combines deals from all sources
    """
    logger.info("Starting deal aggregation from all sources")
    reddit_deals = fetch_reddit_deals()
    rss_deals = fetch_rss_deals()
    
    combined = reddit_deals + rss_deals
    logger.info(f"Total aggregated deals: {len(combined)}")
    return combined
