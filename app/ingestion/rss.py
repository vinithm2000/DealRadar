import feedparser
import time
from app.utils.logger import logger

# Verified, working RSS/Atom feeds for Indian deals
FEEDS = {
    "desidime": "https://www.desidime.com/deals.atom",
    "desidime_disc": "https://www.desidime.com/discussions.atom",
    "mashable_deals": "https://mashable.com/feeds/channel/deals",
    "smartprix": "https://www.smartprix.com/bytes/feed/",
    "91mobiles": "https://www.91mobiles.com/hub/feed/",
    "digit": "https://www.digit.in/digit-deals/feed",
    "indianexpress_tech": "https://indianexpress.com/section/technology/feed/",
}

def fetch_rss_deals():
    """
    Fetches deals from verified RSS/Atom feeds
    """
    all_deals = []
    now = time.time()
    
    for name, url in FEEDS.items():
        try:
            logger.info(f"Fetching deals from RSS ({name})")
            feed = feedparser.parse(url)
            
            if not feed.entries:
                logger.info(f"No entries found for RSS feed '{name}'")
                continue
                
            for entry in feed.entries:
                title = getattr(entry, 'title', 'No Title')
                link = getattr(entry, 'link', '')
                
                if not title or not link:
                    continue

                # Convert struct_time to UNIX timestamp
                unix_ts = None
                for ts_field in ['published_parsed', 'updated_parsed']:
                    ts = entry.get(ts_field)
                    if ts:
                        try:
                            unix_ts = time.mktime(ts)
                        except (OverflowError, ValueError):
                            pass
                        break
                
                # Skip if no timestamp or older than 48 hours
                if unix_ts is None:
                    unix_ts = now  # Assume current if no date
                
                age_hours = (now - unix_ts) / 3600
                if age_hours > 48:
                    continue
                
                all_deals.append({
                    "title": title,
                    "url": link,
                    "source": f"rss_{name}",
                    "timestamp": unix_ts
                })
            
            logger.info(f"Fetched {len(feed.entries)} entries from {name}, kept recent ones")
        except Exception as e:
            logger.error(f"Error fetching RSS deals from {name}: {e}")
            
    logger.info(f"Total recent RSS deals: {len(all_deals)}")
    return all_deals
