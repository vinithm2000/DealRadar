from app.utils.logger import logger

# Keywords for India-specific tech niche
KEYWORDS = [
    "mobile", "laptop", "earbuds", "tv", "ssd", "ram", "gpu", 
    "monitor", "keyboard", "mouse", "smartphone", "iphone", 
    "samsung", "oneplus", "asus", "dell", "hp", "lenovo",
    "amazon", "flipkart", "deal", "offer", "sale", "price", "off"
]

# Blacklisted keywords
BLACKLIST = ["refurbished", "pre-owned", "used", "fake", "replica"]

def is_valid_deal(deal):
    """
    Checks if a deal is relevant based on keywords and blacklist
    """
    title = deal["title"].lower()
    
    # Check blacklist
    if any(k in title for k in BLACKLIST):
        logger.debug(f"Deal blacklisted: {deal['title']}")
        return False
        
    # Check if any interest keyword matches
    has_keyword = any(k in title for k in KEYWORDS)
    
    if not has_keyword:
        logger.debug(f"Deal filtered out (no keywords): {deal['title']}")
        
    return has_keyword
