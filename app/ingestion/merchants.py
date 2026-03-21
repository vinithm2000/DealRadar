"""
Merchant deal sources that produce actual amazon.in/flipkart.com URLs.
Uses deal aggregator APIs and affiliate network feeds instead of direct scraping
(which gets blocked by Amazon/Flipkart bot protection).
"""
import requests
import time
import re
import json
from app.utils.logger import logger

def fetch_merchant_deals():
    """
    Fetches deals with actual merchant URLs from multiple reliable sources.
    """
    all_deals = []
    
    # 1. DesiDime API deals
    all_deals.extend(_fetch_desidime_api_deals())
    
    # 2. IndiaDeals / MySmartPrice type APIs
    all_deals.extend(_fetch_deal_apis())
    
    # 3. Extract merchant URLs from RSS content we already have
    all_deals.extend(_fetch_affiliate_feeds())
    
    logger.info(f"MerchantScraper: Total {len(all_deals)} deals with merchant URLs")
    return all_deals

def _fetch_desidime_api_deals():
    """
    DesiDime exposes deal data with merchant URLs in their Atom content.
    This extracts the actual buy URLs from the feed content.
    """
    deals = []
    now = time.time()
    merchants = ['amazon.in', 'flipkart.com', 'myntra.com', 'ajio.com', 'meesho.com',
                 'nykaa.com', 'croma.com', 'jiomart.com', 'tatacliq.com',
                 'amzn.to', 'amzn.in', 'dl.flipkart.com', 'fkrt.it']
    
    try:
        import feedparser
        logger.info("MerchantScraper: Parsing DesiDime for merchant URLs")
        
        feed = feedparser.parse('https://www.desidime.com/deals.atom')
        
        for entry in feed.entries:
            title = getattr(entry, 'title', '')
            original_link = getattr(entry, 'link', '')
            
            if not title:
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
            
            # Skip old
            if (now - unix_ts) / 3600 > 72:
                continue
            
            # Search for merchant URLs in entry content
            content_text = ""
            if hasattr(entry, 'content') and entry.content:
                for c in entry.content:
                    content_text += c.get('value', '') + " "
            if hasattr(entry, 'summary'):
                content_text += getattr(entry, 'summary', '') + " "
            
            # Also check for 'links' array in entry
            if hasattr(entry, 'links'):
                for link in entry.links:
                    href = link.get('href', '')
                    content_text += href + " "
            
            # Find merchant URLs using regex
            merchant_url = None
            for m in merchants:
                pattern = rf'https?://(?:www\.)?{re.escape(m)}/[^\s\'"<>\)]+' 
                match = re.search(pattern, content_text, re.IGNORECASE)
                if match:
                    merchant_url = match.group(0).rstrip('.,;')
                    break
            
            if merchant_url:
                deals.append({
                    "title": title,
                    "url": merchant_url,
                    "source": "desidime_merchant",
                    "timestamp": unix_ts,
                })
                logger.debug(f"MerchantScraper: Extracted {merchant_url[:60]} from DesiDime")
    
    except Exception as e:
        logger.error(f"MerchantScraper DesiDime error: {e}")
    
    logger.info(f"MerchantScraper: {len(deals)} merchant URLs from DesiDime content")
    return deals

def _fetch_deal_apis():
    """
    Fetch from deal aggregator APIs that return direct merchant URLs.
    """
    deals = []
    now = time.time()
    
    apis = [
        {
            "name": "desidime_json",
            "url": "https://www.desidime.com/selective_deals?utf8=✓&search%5Bcategory%5D=&search%5Bq%5D=&search%5Bsort_by%5D=new",
            "headers": {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            },
        },
    ]
    
    for api in apis:
        try:
            logger.info(f"MerchantScraper: Trying {api['name']}")
            resp = requests.get(api['url'], headers=api.get('headers', {}), timeout=15)
            
            if resp.status_code == 200:
                # Try to parse as JSON
                try:
                    data = resp.json() if 'json' in resp.headers.get('content-type', '') else None
                except:
                    data = None
                
                if not data:
                    # Try to extract from HTML response
                    html = resp.text
                    # Look for deal links
                    merchant_patterns = [
                        r'href="(https?://(?:www\.)?amazon\.in/[^"]+)"',
                        r'href="(https?://(?:www\.)?flipkart\.com/[^"]+)"',
                        r'href="(https?://amzn\.to/[^"]+)"',
                        r'href="(https?://dl\.flipkart\.com/[^"]+)"',
                        r'href="(https?://fkrt\.it/[^"]+)"',
                        r'href="(https?://(?:www\.)?myntra\.com/[^"]+)"',
                    ]
                    
                    found_urls = set()
                    for pattern in merchant_patterns:
                        matches = re.findall(pattern, html)
                        for url in matches:
                            found_urls.add(url)
                    
                    for url in list(found_urls)[:20]:
                        deals.append({
                            "title": f"Deal from {api['name']}",
                            "url": url,
                            "source": f"api_{api['name']}",
                            "timestamp": now,
                        })
                elif isinstance(data, list):
                    for d in data[:20]:
                        url = d.get('buy_url') or d.get('merchant_url') or d.get('url', '')
                        title = d.get('title') or d.get('name', 'Deal')
                        if url:
                            deals.append({
                                "title": title,
                                "url": url,
                                "source": f"api_{api['name']}",
                                "timestamp": now,
                            })
                elif isinstance(data, dict):
                    items = data.get('deals', data.get('data', data.get('items', [])))
                    if isinstance(items, list):
                        for d in items[:20]:
                            url = d.get('buy_url') or d.get('merchant_url') or d.get('url', '')
                            title = d.get('title') or d.get('name', 'Deal')
                            if url:
                                deals.append({
                                    "title": title,
                                    "url": url,
                                    "source": f"api_{api['name']}",
                                    "timestamp": now,
                                })
            else:
                logger.info(f"MerchantScraper: {api['name']} returned {resp.status_code}")
                
        except Exception as e:
            logger.error(f"MerchantScraper {api['name']} error: {e}")
    
    logger.info(f"MerchantScraper: {len(deals)} deals from APIs")
    return deals

def _fetch_affiliate_feeds():
    """
    Fetch from known affiliate deal feeds that contain direct merchant URLs.
    These are deal sites that expose RSS with actual product links.
    """
    deals = []
    now = time.time()
    
    feeds_with_merchant_links = [
        {
            "name": "indiafreestuff",
            "url": "https://www.indiafreestuff.in/feed",
        },
        {
            "name": "freekaamaal",
            "url": "https://www.freekaamaal.com/feed",
        },
        {
            "name": "coupondunia",
            "url": "https://www.coupondunia.in/blog/feed/",
        },
    ]
    
    merchants = ['amazon.in', 'flipkart.com', 'myntra.com', 'ajio.com', 'meesho.com',
                 'amzn.to', 'dl.flipkart.com', 'fkrt.it']
    
    for feed_info in feeds_with_merchant_links:
        try:
            import feedparser
            logger.info(f"MerchantScraper: Checking {feed_info['name']} for merchant URLs")
            feed = feedparser.parse(feed_info['url'])
            
            for entry in feed.entries[:30]:
                title = getattr(entry, 'title', '')
                link = getattr(entry, 'link', '')
                
                # Check if the main link is a merchant URL
                for m in merchants:
                    if m in link:
                        deals.append({
                            "title": title,
                            "url": link,
                            "source": f"feed_{feed_info['name']}",
                            "timestamp": now,
                        })
                        break
                else:
                    # Search in content for merchant URLs
                    content = ""
                    if hasattr(entry, 'content') and entry.content:
                        for c in entry.content:
                            content += c.get('value', '')
                    if hasattr(entry, 'summary'):
                        content += getattr(entry, 'summary', '')
                    
                    for m in merchants:
                        pattern = rf'https?://(?:www\.)?{re.escape(m)}/[^\s\'"<>\)]+' 
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            merchant_url = match.group(0).rstrip('.,;')
                            deals.append({
                                "title": title,
                                "url": merchant_url,
                                "source": f"feed_{feed_info['name']}",
                                "timestamp": now,
                            })
                            break
                            
        except Exception as e:
            logger.error(f"MerchantScraper {feed_info['name']} error: {e}")
    
    logger.info(f"MerchantScraper: {len(deals)} from affiliate feeds")
    return deals
