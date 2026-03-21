from app.utils.logger import logger

def aggregate_all_sources():
    """
    Combines deals from all sources.
    Each source is isolated so one failure doesn't crash others.
    """
    all_deals = []
    
    # Reddit
    try:
        from .reddit import fetch_reddit_deals
        reddit_deals = fetch_reddit_deals()
        all_deals.extend(reddit_deals)
        logger.info(f"Aggregator: {len(reddit_deals)} deals from Reddit")
    except Exception as e:
        logger.error(f"Aggregator: Reddit source failed: {e}")
    
    # RSS feeds
    try:
        from .rss import fetch_rss_deals
        rss_deals = fetch_rss_deals()
        all_deals.extend(rss_deals)
        logger.info(f"Aggregator: {len(rss_deals)} deals from RSS")
    except Exception as e:
        logger.error(f"Aggregator: RSS source failed: {e}")
    
    logger.info(f"Aggregator: Total {len(all_deals)} deals from all sources")
    return all_deals
