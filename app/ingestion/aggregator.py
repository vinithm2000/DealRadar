from app.utils.logger import logger

def aggregate_all_sources():
    """
    Combines deals from all sources.
    Each source is isolated so one failure doesn't crash others.
    """
    all_deals = []
    
    # 1. Direct merchant deals (Amazon, Flipkart) - these get EarnKaro links
    try:
        from .merchants import fetch_merchant_deals
        merchant_deals = fetch_merchant_deals()
        all_deals.extend(merchant_deals)
        logger.info(f"Aggregator: {len(merchant_deals)} deals from merchant scrapers")
    except Exception as e:
        logger.error(f"Aggregator: Merchant scraper failed: {e}", exc_info=True)
    
    # 2. Bank Card Offers
    try:
        from .bank_offers import fetch_bank_offers
        bank_deals = fetch_bank_offers()
        all_deals.extend(bank_deals)
        logger.info(f"Aggregator: {len(bank_deals)} bank card offers")
    except Exception as e:
        logger.error(f"Aggregator: Bank offers scraper failed: {e}", exc_info=True)
        
    # 3. Reddit deals
    try:
        from .reddit import fetch_reddit_deals
        reddit_deals = fetch_reddit_deals()
        all_deals.extend(reddit_deals)
        logger.info(f"Aggregator: {len(reddit_deals)} deals from Reddit")
    except Exception as e:
        logger.error(f"Aggregator: Reddit source failed: {e}", exc_info=True)
    
    # 4. RSS/Atom feeds  
    try:
        from .rss import fetch_rss_deals
        rss_deals = fetch_rss_deals()
        all_deals.extend(rss_deals)
        logger.info(f"Aggregator: {len(rss_deals)} deals from RSS")
    except Exception as e:
        logger.error(f"Aggregator: RSS source failed: {e}", exc_info=True)

    
    logger.info(f"Aggregator: Total {len(all_deals)} deals from all sources")
    return all_deals
