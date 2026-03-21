import requests
import time
import urllib.parse
from app.utils.config import config
from app.utils.logger import logger

# All EarnKaro partner merchants (from their Partners page)
SUPPORTED_MERCHANTS = [
    # Top partners
    "amazon.in", "amazon.com", "amzn.to", "amzn.in",
    "flipkart.com", "dl.flipkart.com",
    "myntra.com",
    "ajio.com",
    "meesho.com",
    "nykaa.com", "nykaafashion.com",
    "croma.com",
    "reliancedigital.in",
    "tatacliq.com",
    "jiomart.com",
    "snapdeal.com",
    # Fashion & Beauty
    "bewakoof.com",
    "shoppersstop.com",
    "bata.in",
    "lenskart.com",
    "mamaearth.in",
    "myglamm.com",
    "purplle.com",
    "thedermaco.com",
    "mcaffeine.com",
    "dotandkey.com",
    "wowskinscience.com",
    # Electronics
    "boat-lifestyle.com",
    "crossbeats.com",
    "zebronics.com",
    "samsung.com/in",
    # Home & Kitchen
    "pepperfry.com",
    "urbanladder.com",
    "sleepycat.in",
    "wakefit.co",
    # Food & Grocery
    "bigbasket.com",
    "swiggy.com",
    "zomato.com",
    # Others
    "pharmeasy.in",
    "netmeds.com",
    "1mg.com",
    "booking.com",
    "makemytrip.com",
    "goibibo.com",
    "cleartrip.com",
]

# Cache for EarnKaro API token
_api_token = None
_token_expires = 0

def _is_merchant_url(url):
    """Check if URL is from a supported EarnKaro partner"""
    url_lower = url.lower()
    for merchant in SUPPORTED_MERCHANTS:
        if merchant in url_lower:
            return True
    return False

def _try_earnkaro_api(url):
    """
    Try EarnKaro's link creation API.
    Uses email/password login to get a session, then converts the link.
    """
    global _api_token, _token_expires
    
    email = config.EARNKARO_EMAIL
    password = config.EARNKARO_PASSWORD
    
    if not email or not password:
        return None
    
    try:
        # Login if needed
        if not _api_token or time.time() > _token_expires:
            login_urls = [
                "https://earnkaro.com/api/v1/auth/login",
                "https://ekapi.earnkaro.com/api/auth/login",
            ]
            
            for login_url in login_urls:
                try:
                    resp = requests.post(
                        login_url,
                        json={"email": email, "password": password},
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        _api_token = (
                            data.get("token") or 
                            data.get("data", {}).get("token") or
                            data.get("access_token")
                        )
                        if _api_token:
                            _token_expires = time.time() + 3500
                            logger.info(f"EarnKaro: Login OK via {login_url}")
                            break
                except:
                    continue
        
        if not _api_token:
            return None
        
        # Try link conversion
        convert_urls = [
            "https://earnkaro.com/api/v1/create_link",
            "https://ekapi.earnkaro.com/api/link/convert",
        ]
        
        for convert_url in convert_urls:
            try:
                resp = requests.post(
                    convert_url,
                    json={"url": url, "api_key": config.EARNKARO_ID},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {_api_token}"
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    link = (
                        data.get("link") or 
                        data.get("data", {}).get("link") or
                        data.get("convertedUrl") or
                        data.get("data", {}).get("convertedUrl") or
                        data.get("profit_link")
                    )
                    if link:
                        logger.info(f"EarnKaro API: Converted {url[:50]}")
                        return link
            except:
                continue
        
        return None
    except Exception as e:
        logger.warning(f"EarnKaro API error: {e}")
        return None

def _make_redirect_link(url):
    """
    Create an EarnKaro affiliate link using their redirect format.
    This is the fallback when API is not available.
    Format: https://ekaro.in/enkr{EARNKARO_ID}?url={encoded_url}
    """
    earnkaro_id = config.EARNKARO_ID
    if not earnkaro_id or earnkaro_id == "YOUR_ID":
        logger.warning("EarnKaro ID not configured")
        return None
    
    encoded_url = urllib.parse.quote(url, safe='')
    # Use the known redirect format
    affiliate_url = f"https://ekaro.in/enkr{earnkaro_id}?url={encoded_url}"
    return affiliate_url

def generate_affiliate_link(url):
    """
    Convert a URL to an EarnKaro affiliate link.
    Strategy:
    1. Check if URL is from a supported merchant
    2. Try EarnKaro API first
    3. Fallback to redirect URL format
    """
    if not url:
        return url
    
    # Only convert merchant URLs
    if not _is_merchant_url(url):
        return url
    
    # Try API first
    api_link = _try_earnkaro_api(url)
    if api_link:
        return api_link
    
    # Fallback to redirect format
    redirect_link = _make_redirect_link(url)
    if redirect_link:
        logger.info(f"EarnKaro redirect: {url[:50]} -> ekaro.in/...")
        return redirect_link
    
    return url
