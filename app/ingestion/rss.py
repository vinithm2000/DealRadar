import feedparser
from app.utils.logger import logger

FEEDS = {
    "desidime": "https://www.desidime.com/new",
    "slickdeals": "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first",
    "coupondunia": "https://www.coupondunia.in/blog/feed/" # Representative RSS
}

def fetch_rss_deals():
    """
    Fetches deals from various RSS feeds
    """
    all_deals = []
    
    for name, url in FEEDS.items():
        try:
            logger.info(f"Fetching deals from RSS ({name}): {url}")
            feed = feedparser.parse(url)
            
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"RSS feed '{name}' may be malformed: {feed.bozo_exception}")
            
            if not feed.entries:
                logger.info(f"No entries found for RSS feed '{name}'")
                continue
                
            for entry in feed.entries:
                # Convert struct_time to UNIX timestamp
                ts = entry.get("published_parsed")
                unix_ts = None
                if ts:
                    import time
                    unix_ts = time.mktime(ts)

                all_deals.append({
                    "title": getattr(entry, 'title', 'No Title'),
                    "url": getattr(entry, 'link', ''),
                    "source": f"rss_{name}",
                    "timestamp": unix_ts
                })
            
            logger.info(f"Fetched {len(feed.entries)} deals from {name}")
        except Exception as e:
            logger.error(f"Error fetching RSS deals from {name}: {e}")
            
    return all_deals
