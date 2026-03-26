"""
Bank card offer alerts scraper.
Scrapes weekly bank offers from e-commerce sites.
HDFC, SBI, ICICI, Axis, Kotak offers on Amazon, Flipkart, etc.
"""
import requests
import re
import time
from app.utils.logger import logger

# Bank offer sources
BANK_OFFER_FEEDS = [
    {
        "name": "desidime_bank",
        "url": "https://www.desidime.com/discussions.atom",
        "search_terms": ["hdfc", "sbi", "icici", "axis", "kotak", "bank", "card offer", 
                        "credit card", "debit card", "cashback", "emi"],
    },
]

def fetch_bank_offers():
    """
    Fetch bank card offers from deal feeds.
    Filters for bank-specific deals (HDFC, SBI, ICICI, Axis, Kotak).
    """
    deals = []
    now = time.time()
    
    # 1. Search DesiDime for bank offers
    try:
        import feedparser
        logger.info("BankOffers: Searching for bank card offers")
        
        feed = feedparser.parse("https://www.desidime.com/discussions.atom")
        bank_keywords = ["hdfc", "sbi", "icici", "axis", "kotak", "bank offer", 
                        "credit card deal", "card offer", "bank cashback", "emi no cost"]
        
        for entry in feed.entries:
            title = getattr(entry, 'title', '').lower()
            link = getattr(entry, 'link', '')
            
            # Check if title mentions bank offers
            is_bank = any(kw in title for kw in bank_keywords)
            if not is_bank:
                continue
            
            # Parse timestamp
            unix_ts = now
            for ts_field in ['published_parsed', 'updated_parsed']:
                ts = entry.get(ts_field)
                if ts:
                    try:
                        unix_ts = time.mktime(ts)
                    except:
                        pass
                    break
            
            # Bank offers are usually valid for a week, so extend age limit
            if (now - unix_ts) / 3600 > 168:  # 7 days
                continue
            
            deals.append({
                "title": f"🏦 {entry.title}",
                "url": link,
                "source": "bank_offers",
                "timestamp": unix_ts,
            })
    
    except Exception as e:
        logger.error(f"BankOffers: DesiDime error: {e}")
    
    # 2. Also search other deal feeds
    bank_feed_urls = [
        "https://www.indiafreestuff.in/feed",
        "https://www.freekaamaal.com/feed",
    ]
    
    for feed_url in bank_feed_urls:
        try:
            import feedparser
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:30]:
                title = getattr(entry, 'title', '').lower()
                if any(kw in title for kw in ["hdfc", "sbi", "icici", "axis", "kotak", "bank", "card"]):
                    deals.append({
                        "title": f"🏦 {entry.title}",
                        "url": getattr(entry, 'link', ''),
                        "source": "bank_offers",
                        "timestamp": now,
                    })
        except Exception as e:
            logger.error(f"BankOffers feed error: {e}")
    
    logger.info(f"BankOffers: Found {len(deals)} bank card offers")
    return deals
