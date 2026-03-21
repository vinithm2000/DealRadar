import feedparser
import time
import re
import requests
from app.utils.logger import logger

# RSS/Atom feeds
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

# Merchant URL patterns to look for in feed content
MERCHANT_PATTERNS = [
    r'https?://(?:www\.)?amazon\.in/[^\s\'"<>]+',
    r'https?://(?:www\.)?flipkart\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?myntra\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?ajio\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?meesho\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?croma\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?nykaa\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?jiomart\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?tatacliq\.com/[^\s\'"<>]+',
    r'https?://(?:www\.)?reliancedigital\.in/[^\s\'"<>]+',
    r'https?://amzn\.to/[^\s\'"<>]+',
    r'https?://dl\.flipkart\.com/[^\s\'"<>]+',
]

# Combined regex for speed
_MERCHANT_RE = re.compile('|'.join(MERCHANT_PATTERNS), re.IGNORECASE)

def _extract_merchant_url_from_content(entry):
    """
    Extract a merchant URL from the RSS entry's content/summary fields.
    DesiDime Atom feeds include the actual deal links in the HTML content.
    """
    # Check various content fields
    content_text = ""
    
    # feedparser content field (Atom)
    if hasattr(entry, 'content') and entry.content:
        for c in entry.content:
            content_text += c.get('value', '') + " "
    
    # summary/description field (RSS)
    if hasattr(entry, 'summary'):
        content_text += getattr(entry, 'summary', '') + " "
    
    if hasattr(entry, 'description'):
        content_text += getattr(entry, 'description', '') + " "
    
    if not content_text:
        return None
    
    # Search for merchant URLs in content
    matches = _MERCHANT_RE.findall(content_text)
    if matches:
        # Return the first merchant URL found, clean it up
        url = matches[0].rstrip('.')
        return url
    
    return None

def _scrape_amazon_todays_deals():
    """
    Scrape Amazon India Today's Deals page for direct deal links.
    These are guaranteed merchant URLs that EarnKaro can convert.
    """
    deals = []
    try:
        logger.info("Scraping Amazon India Today's Deals")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-IN,en;q=0.9",
        }
        
        # Amazon Deals RSS feed
        resp = requests.get(
            "https://www.amazon.in/gp/rss/movers-and-shakers",
            headers=headers, timeout=15
        )
        
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            now = time.time()
            
            for entry in feed.entries[:20]:
                title = getattr(entry, 'title', '')
                link = getattr(entry, 'link', '')
                if title and link and 'amazon.in' in link:
                    deals.append({
                        "title": f"🏷️ {title}",
                        "url": link,
                        "source": "amazon_deals",
                        "timestamp": now
                    })
            
            logger.info(f"Amazon: Got {len(deals)} deals")
        else:
            logger.warning(f"Amazon RSS returned {resp.status_code}")
    except Exception as e:
        logger.error(f"Amazon scrape error: {e}")
    
    return deals

def fetch_rss_deals():
    """
    Fetches deals from all RSS/Atom feeds.
    For DesiDime feeds, extracts actual merchant URLs from the feed content.
    """
    all_deals = []
    now = time.time()
    
    for name, url in FEEDS.items():
        try:
            logger.info(f"RSS: Fetching {name}")
            feed = feedparser.parse(url)
            
            if not feed.entries:
                logger.info(f"RSS: No entries from {name}")
                continue
            
            count = 0
            merchant_count = 0
            
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
                
                age_hours = (now - unix_ts) / 3600
                if age_hours > 72:
                    continue
                
                # For DesiDime, try to extract merchant URL from content
                final_url = link
                if 'desidime' in name:
                    merchant_url = _extract_merchant_url_from_content(entry)
                    if merchant_url:
                        final_url = merchant_url
                        merchant_count += 1
                
                all_deals.append({
                    "title": title,
                    "url": final_url,
                    "source": f"rss_{name}",
                    "timestamp": unix_ts
                })
                count += 1
            
            if merchant_count > 0:
                logger.info(f"RSS: {name} - {count} deals, {merchant_count} with merchant URLs extracted")
            else:
                logger.info(f"RSS: {name} - {count} recent deals")
                
        except Exception as e:
            logger.error(f"RSS: Error fetching {name}: {e}")
    
    # Also get Amazon Today's Deals
    amazon_deals = _scrape_amazon_todays_deals()
    all_deals.extend(amazon_deals)
    
    logger.info(f"RSS: Total {len(all_deals)} deals from all feeds + Amazon")
    return all_deals
