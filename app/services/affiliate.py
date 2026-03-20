import requests
import time
from app.utils.config import config
from app.utils.logger import logger

# Session cache
_session_token = None
_session_expires = 0

def _login_earnkaro():
    """
    Login to EarnKaro EK Affiliaters API and get session token
    """
    global _session_token, _session_expires
    
    email = config.EARNKARO_EMAIL
    password = config.EARNKARO_PASSWORD
    
    if not email or not password:
        logger.warning("EarnKaro credentials not configured, using fallback")
        return None
    
    try:
        resp = requests.post(
            "https://ekapi.earnkaro.com/api/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            _session_token = data.get("token") or data.get("data", {}).get("token")
            _session_expires = time.time() + 3500  # Refresh every ~1 hour
            logger.info("EarnKaro: Login successful")
            return _session_token
        else:
            logger.error(f"EarnKaro login failed: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"EarnKaro login error: {e}")
        return None

def _get_token():
    """Get valid session token, login if expired"""
    global _session_token, _session_expires
    if _session_token and time.time() < _session_expires:
        return _session_token
    return _login_earnkaro()

def _convert_via_api(url):
    """
    Convert a URL to an EarnKaro affiliate link via their API
    """
    token = _get_token()
    if not token:
        return None
    
    try:
        resp = requests.post(
            "https://ekapi.earnkaro.com/api/link/convert",
            json={"url": url},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            affiliate_url = (
                data.get("link") or 
                data.get("data", {}).get("link") or
                data.get("convertedUrl") or
                data.get("data", {}).get("convertedUrl")
            )
            if affiliate_url:
                logger.info(f"EarnKaro: Converted {url[:50]}...")
                return affiliate_url
            else:
                logger.warning(f"EarnKaro: No link in response: {data}")
                return None
        else:
            logger.warning(f"EarnKaro convert failed ({resp.status_code}): {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"EarnKaro convert error: {e}")
        return None

def _fallback_link(url):
    """
    Fallback: manual URL wrapping for supported merchants
    """
    affiliate_id = config.EARNKARO_ID
    supported = [
        "amazon.in", "flipkart.com", "myntra.com", "meesho.com",
        "ajio.com", "nykaa.com", "croma.com", "reliancedigital.in"
    ]
    
    for merchant in supported:
        if merchant in url:
            return f"https://ekaro.in/{affiliate_id}?url={url}"
    
    return url  # Return original if unsupported

def generate_affiliate_link(url):
    """
    Convert a URL to an EarnKaro affiliate link.
    Tries API first, falls back to manual wrapping.
    """
    if not url:
        return None
    
    # Try API conversion first
    converted = _convert_via_api(url)
    if converted:
        return converted
    
    # Fallback to manual wrapping
    return _fallback_link(url)
