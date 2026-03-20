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

# Minimum recency (48 hours)
MAX_AGE_HOURS = 48

def is_valid_deal(deal):
    """
    Checks if a deal passes keyword and blacklist filters
    """
    title = deal["title"].lower()
    
    # 1. Blacklist check
    for b in BLACKLIST:
        if b in title:
            return False
            
    # 2. Keyword check
    found_keyword = False
    for k in KEYWORDS:
        if k in title:
            found_keyword = True
            break
            
    if not found_keyword:
        return False

    # 3. Recency check
    import time
    if deal.get("timestamp"):
        age_seconds = time.time() - deal["timestamp"]
        if age_seconds > (MAX_AGE_HOURS * 3600):
            return False
            
    return True
