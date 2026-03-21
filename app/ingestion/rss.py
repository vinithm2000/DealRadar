import feedparser
import time
import requests
from app.utils.logger import logger

# RSS/Atom feeds that actually produce deal content
FEEDS = {
    "desidime_deals": "https://www.desidime.com/deals.atom",
    "desidime_disc": "https://www.desidime.com/discussions.atom",
    "gadgets360": "https://feeds.feedburner.com/gadgets360-latest",
    "smartprix": "https://www.smartprix.com/bytes/feed/",
    "91mobiles": "https://www.91mobiles.com/hub/feed/",
    "indianexpress_tech": "https://indianexpress.com/section/technology/feed/",
    "digit_deals": "https://www.digit.in/digit-deals/feed",
    "fonearena": "https://www.fonearena.com/blog/feed",
    "techpp": "https://techpp.com/feed/",
}

# Direct deal aggregator APIs / pages
DEAL_APIS = [
    {
        "name": "amazon_deals",
        "url": "https://www.amazon.in/gp/rss/bestsellers",
        "type": "rss"
    },
]

def _fetch_single_feed(name, url, now):
    """Fetch deals from a single RSS/Atom feed"""
    deals = []
    try:
        logger.info(f"RSS: Fetching {name}")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            logger.info(f"RSS: No entries from {name}")
            return deals
        
        for entry in feed.entries:
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            
            if not title or not link:
                continue

            # Parse timestamp
            unix_ts = None
            for ts_field in ['published_parsed', 'updated_parsed']:
                ts = entry.get(ts_field)
                if ts:
                    try:
                        unix_ts = time.mktime(ts)
                    except (OverflowError, ValueError):
                        pass
                    break
            
            if unix_ts is None:
                unix_ts = now
            
            # Skip very old content
            age_hours = (now - unix_ts) / 3600
            if age_hours > 72:
                continue
            
            deals.append({
                "title": title,
                "url": link,
                "source": f"rss_{name}",
                "timestamp": unix_ts
            })
        
        logger.info(f"RSS: Got {len(deals)} recent entries from {name}")
    except Exception as e:
        logger.error(f"RSS: Error fetching {name}: {e}")
    
    return deals

def fetch_rss_deals():
    """
    Fetches deals from all RSS/Atom feeds.
    No more DesiDime scraping - too slow and unreliable.
    """
    all_deals = []
    now = time.time()
    
    # Fetch from RSS feeds
    for name, url in FEEDS.items():
        deals = _fetch_single_feed(name, url, now)
        all_deals.extend(deals)
    
    # Fetch from deal APIs
    for api in DEAL_APIS:
        deals = _fetch_single_feed(api["name"], api["url"], now)
        all_deals.extend(deals)
    
    logger.info(f"RSS: Total {len(all_deals)} recent deals from all feeds")
    return all_deals
