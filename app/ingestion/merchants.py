"""
Direct merchant deal scrapers.
These produce actual amazon.in / flipkart.com URLs that EarnKaro can convert.
"""
import requests
import time
import re
from app.utils.logger import logger

def fetch_merchant_deals():
    """
    Fetches deals directly from merchant websites and deal aggregator APIs.
    Returns deals with direct merchant URLs (amazon.in, flipkart.com, etc.)
    """
    all_deals = []
    
    # 1. Amazon India deals
    amazon_deals = _scrape_amazon_deals()
    all_deals.extend(amazon_deals)
    
    # 2. Flipkart deals 
    flipkart_deals = _scrape_flipkart_deals()
    all_deals.extend(flipkart_deals)
    
    # 3. DesiDime API (returns merchant URLs directly)
    desidime_deals = _fetch_desidime_api()
    all_deals.extend(desidime_deals)
    
    logger.info(f"MerchantScraper: Total {len(all_deals)} direct merchant deals")
    return all_deals

def _scrape_amazon_deals():
    """Scrape Amazon India for trending/bestseller deals"""
    deals = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    # Amazon Best Sellers pages by category
    amazon_pages = [
        ("https://www.amazon.in/gp/bestsellers/electronics", "Electronics"),
        ("https://www.amazon.in/gp/bestsellers/computers", "Computers"),
        ("https://www.amazon.in/gp/bestsellers/shoes", "Fashion"),
        ("https://www.amazon.in/gp/bestsellers/kitchen", "Home"),
        ("https://www.amazon.in/gp/movers-and-shakers/electronics", "Electronics Trending"),
    ]
    
    now = time.time()
    
    for page_url, category in amazon_pages:
        try:
            logger.info(f"Amazon: Scraping {category}")
            resp = requests.get(page_url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                logger.warning(f"Amazon: {category} returned {resp.status_code}")
                continue
            
            html = resp.text
            
            # Extract product links and titles from Amazon HTML
            # Pattern: /dp/ASIN or /gp/product/ASIN
            product_pattern = r'<a[^>]*href="(/(?:dp|gp/product)/[A-Z0-9]{10}[^"]*)"[^>]*>\s*<(?:span|div)[^>]*class="[^"]*(?:p13n-sc-truncate|_cDEzb_p13n-sc-css-line-clamp-1)[^"]*"[^>]*>([^<]+)<'
            
            matches = re.findall(product_pattern, html, re.DOTALL)
            
            if not matches:
                # Try simpler pattern
                url_pattern = r'href="(/dp/[A-Z0-9]{10}[^"]*)"'
                title_pattern = r'class="[^"]*p13n-sc-truncate[^"]*"[^>]*>([^<]+)<'
                
                urls = re.findall(url_pattern, html)
                titles = re.findall(title_pattern, html)
                
                for i, url_path in enumerate(urls[:15]):
                    title = titles[i].strip() if i < len(titles) else f"Amazon {category} Deal #{i+1}"
                    full_url = f"https://www.amazon.in{url_path.split('?')[0]}"
                    
                    deals.append({
                        "title": f"🏷️ {title}",
                        "url": full_url,
                        "source": f"amazon_{category.lower().replace(' ', '_')}",
                        "timestamp": now,
                    })
            else:
                for url_path, title in matches[:15]:
                    full_url = f"https://www.amazon.in{url_path.split('?')[0]}"
                    deals.append({
                        "title": f"🏷️ {title.strip()}",
                        "url": full_url,
                        "source": f"amazon_{category.lower().replace(' ', '_')}",
                        "timestamp": now,
                    })
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Amazon {category} error: {e}")
    
    logger.info(f"Amazon: Got {len(deals)} product deals")
    return deals

def _scrape_flipkart_deals():
    """Scrape Flipkart for deal-of-the-day and top offers"""
    deals = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    
    now = time.time()
    
    try:
        logger.info("Flipkart: Scraping deals")
        resp = requests.get(
            "https://www.flipkart.com/offers-store",
            headers=headers, timeout=15
        )
        
        if resp.status_code == 200:
            html = resp.text
            
            # Extract Flipkart product links
            # Pattern: /product-name/p/itm...
            fk_pattern = r'href="(/[^"]+/p/itm[^"]+)"'
            title_matches = re.findall(r'class="[^"]*(?:IRpwTa|_2WkVRV|css-1qaijid)[^"]*"[^>]*>([^<]+)<', html)
            url_matches = re.findall(fk_pattern, html)
            
            for i, url_path in enumerate(url_matches[:15]):
                title = title_matches[i].strip() if i < len(title_matches) else f"Flipkart Deal #{i+1}"
                full_url = f"https://www.flipkart.com{url_path}"
                
                deals.append({
                    "title": f"🛍️ {title}",
                    "url": full_url,
                    "source": "flipkart_deals",
                    "timestamp": now,
                })
        else:
            logger.warning(f"Flipkart: Returned {resp.status_code}")
            
    except Exception as e:
        logger.error(f"Flipkart error: {e}")
    
    logger.info(f"Flipkart: Got {len(deals)} deals")
    return deals

def _fetch_desidime_api():
    """
    Fetch deals from DesiDime's API.
    Their API returns deal data with the actual merchant redirect URLs.
    """
    deals = []
    now = time.time()
    
    try:
        logger.info("DesiDime API: Fetching deals")
        headers = {
            "User-Agent": "DealRadarBot/2.0",
            "Accept": "application/json",
        }
        
        # DesiDime has a JSON feed/API
        resp = requests.get(
            "https://www.desidime.com/deals.json",
            headers=headers, timeout=15
        )
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                deal_list = data if isinstance(data, list) else data.get('deals', data.get('data', []))
                
                for d in deal_list[:20]:
                    if isinstance(d, dict):
                        title = d.get('title') or d.get('name', '')
                        # Look for the actual merchant URL
                        url = (
                            d.get('buy_url') or 
                            d.get('merchant_url') or 
                            d.get('url') or  
                            d.get('link', '')
                        )
                        
                        if title and url:
                            deals.append({
                                "title": title,
                                "url": url,
                                "source": "desidime_api",
                                "timestamp": now,
                            })
            except (ValueError, KeyError) as e:
                logger.warning(f"DesiDime API parse error: {e}")
        else:
            logger.info(f"DesiDime API: Returned {resp.status_code}")
            
    except Exception as e:
        logger.error(f"DesiDime API error: {e}")
    
    logger.info(f"DesiDime API: Got {len(deals)} deals")
    return deals
