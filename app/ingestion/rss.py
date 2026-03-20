import feedparser
import time
import requests
from bs4 import BeautifulSoup
from app.utils.logger import logger

# RSS/Atom feeds - focused on sources that link to actual merchant pages
FEEDS = {
    "desidime_deals": "https://www.desidime.com/deals.atom",
    "smartprix": "https://www.smartprix.com/bytes/feed/",
    "91mobiles": "https://www.91mobiles.com/hub/feed/",
    "digit_deals": "https://www.digit.in/digit-deals/feed",
    "indianexpress_tech": "https://indianexpress.com/section/technology/feed/",
    "gadgets360": "https://feeds.feedburner.com/gadgets360-latest",
}

# Amazon India deal pages to scrape
AMAZON_DEAL_PAGES = [
    "https://www.amazon.in/gp/goldbox",
    "https://www.amazon.in/deals",
]

def _try_extract_merchant_url(desidime_url):
    """
    Try to extract the actual merchant URL from a DesiDime deal page.
    DesiDime pages contain redirect links to Amazon, Flipkart, etc.
    """
    try:
        headers = {"User-Agent": "DealRadarBot/2.0"}
        resp = requests.get(desidime_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for "Get Deal" or "Buy Now" links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            
            # Check if link goes to a merchant
            merchants = ['amazon.in', 'flipkart.com', 'myntra.com', 'ajio.com', 
                        'meesho.com', 'nykaa.com', 'croma.com', 'jiomart.com']
            for m in merchants:
                if m in href and ('deal' in text or 'buy' in text or 'get' in text or 'shop' in text or 'go to' in text):
                    return href
        
        # Also check for redirect links in common DesiDime format
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            for m in ['amazon.in', 'flipkart.com', 'myntra.com']:
                if m in href:
                    return href
                    
    except Exception as e:
        logger.debug(f"Could not extract merchant URL from {desidime_url}: {e}")
    
    return None

def fetch_rss_deals():
    """
    Fetches deals from RSS/Atom feeds.
    For DesiDime, tries to extract actual merchant URLs.
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
            
            count = 0
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
                
                if unix_ts is None:
                    unix_ts = now
                
                age_hours = (now - unix_ts) / 3600
                if age_hours > 48:
                    continue
                
                # For DesiDime, try to get the actual merchant URL
                final_url = link
                if 'desidime' in name:
                    merchant_url = _try_extract_merchant_url(link)
                    if merchant_url:
                        final_url = merchant_url
                        logger.info(f"Extracted merchant URL from DesiDime: {merchant_url[:60]}")
                
                all_deals.append({
                    "title": title,
                    "url": final_url,
                    "source": f"rss_{name}",
                    "timestamp": unix_ts
                })
                count += 1
            
            logger.info(f"Kept {count} recent deals from {name}")
        except Exception as e:
            logger.error(f"Error fetching RSS deals from {name}: {e}")
            
    logger.info(f"Total recent RSS deals: {len(all_deals)}")
    return all_deals
