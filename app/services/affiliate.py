from app.utils.config import config
from app.utils.logger import logger

def generate_affiliate_link(url):
    """
    Wraps a URL with EarnKaro affiliate link
    """
    if not url:
        return None
        
    # Example EarnKaro format: https://earnkaro.com/r/YOUR_ID?url={url}
    affiliate_id = config.EARNKARO_ID
    
    # Simple URL wrapping (manual pattern)
    if "amazon.in" in url or "flipkart.com" in url or "myntra.com" in url:
        return f"https://earnkaro.com/r/{affiliate_id}?url={url}"
        
    return url # Return original if no specific rule
