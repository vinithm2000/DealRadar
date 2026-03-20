import requests
import time
import urllib.parse
from app.utils.config import config
from app.utils.logger import logger

# Merchants supported by EarnKaro
SUPPORTED_MERCHANTS = [
    "amazon.in", "amazon.com",
    "flipkart.com", 
    "myntra.com", 
    "meesho.com",
    "ajio.com", 
    "nykaa.com", 
    "croma.com", 
    "reliancedigital.in",
    "tatacliq.com",
    "jiomart.com",
    "snapdeal.com",
    "shopclues.com",
    "paytmmall.com",
]

def _is_merchant_url(url):
    """Check if URL is from a supported merchant"""
    url_lower = url.lower()
    for merchant in SUPPORTED_MERCHANTS:
        if merchant in url_lower:
            return True
    return False

def _make_earnkaro_link(url):
    """
    Create an EarnKaro affiliate link using the known redirect format.
    This is the reliable method used by EarnKaro affiliates.
    """
    earnkaro_id = config.EARNKARO_ID
    if not earnkaro_id or earnkaro_id == "YOUR_ID":
        logger.warning("EarnKaro ID not configured")
        return None
    
    encoded_url = urllib.parse.quote(url, safe='')
    affiliate_url = f"https://ekaro.in/enkr{earnkaro_id}?url={encoded_url}"
    return affiliate_url

def generate_affiliate_link(url):
    """
    Convert a URL to an EarnKaro affiliate link.
    Only converts URLs from supported merchants.
    Returns original URL for non-merchant links (like DesiDime, blogs).
    """
    if not url:
        return None
    
    # Only wrap merchant URLs - blog/deal site links won't earn commission
    if _is_merchant_url(url):
        affiliate = _make_earnkaro_link(url)
        if affiliate:
            logger.info(f"EarnKaro: Converted {url[:60]}...")
            return affiliate
    else:
        logger.debug(f"EarnKaro: Skipping non-merchant URL: {url[:60]}")
    
    return url  # Return original for non-merchant URLs
