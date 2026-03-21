from app.utils.logger import logger
import time

# Extremely broad keywords - we want to catch ALL deals
# Any deal mentioning a product, discount, or merchant passes
KEYWORDS = [
    # Discount indicators
    "off", "deal", "offer", "sale", "price", "discount", "coupon", 
    "lowest", "cheapest", "free", "cashback", "flat", "save", "loot",
    "steal", "hurry", "limited", "flash", "bumper", "mega",
    # Price indicators  
    "₹", "rs", "rs.", "inr", "rupee", "%",
    # Merchants
    "amazon", "flipkart", "myntra", "ajio", "meesho", "croma",
    "nykaa", "jiomart", "tatacliq", "snapdeal", "reliancedigital",
    # Electronics
    "mobile", "laptop", "earbuds", "tv", "ssd", "ram", "gpu", 
    "monitor", "keyboard", "mouse", "smartphone", "iphone", 
    "samsung", "oneplus", "asus", "dell", "hp", "lenovo",
    "ipad", "macbook", "tablet", "headphone", "speaker", "smartwatch",
    "charger", "power bank", "camera", "printer", "router",
    "pixel", "redmi", "realme", "nothing", "motorola", "vivo", "oppo",
    "nintendo", "playstation", "xbox", "gaming",
    # Fashion
    "shoes", "clothing", "fashion", "dress", "sneakers", "watch",
    "bag", "wallet", "perfume", 
    # Home
    "furniture", "kitchen", "appliance", "ac", "refrigerator",
    "washing machine", "microwave", "purifier", "mattress",
    # Food
    "zomato", "swiggy", "food", "grocery", "blinkit", "bigbasket",
    # Generic product terms
    "buy", "best", "review", "compare", "specs", "launch", "new",
    "top", "under", "budget",
]

# Blacklisted keywords - only truly spam content
BLACKLIST = [
    "refurbished", "pre-owned", "fake", "replica", "mod apk",
    "hack", "crack", "pirate", "torrent", "survey",
]

# Maximum deal age
MAX_AGE_HOURS = 72  # Increased to 72 hours

def is_valid_deal(deal):
    """
    Checks if a deal passes keyword and blacklist filters.
    Very permissive - we want maximum deals.
    """
    title = deal.get("title", "").lower()
    url = deal.get("url", "").lower()
    combined = title + " " + url
    
    # 1. Blacklist check
    for b in BLACKLIST:
        if b in combined:
            return False
    
    # 2. Auto-pass merchant sources (they're guaranteed real products)
    source = deal.get("source", "").lower()
    if any(s in source for s in ["amazon", "flipkart", "desidime", "deal", "loot", "offer", "merchant"]):
        # Still check recency
        if deal.get("timestamp"):
            age_seconds = time.time() - deal["timestamp"]
            if age_seconds > (MAX_AGE_HOURS * 3600):
                return False
        return True
    
    # 3. Keyword check for other sources - check title AND url
    for k in KEYWORDS:
        if k in combined:
            if deal.get("timestamp"):
                age_seconds = time.time() - deal["timestamp"]
                if age_seconds > (MAX_AGE_HOURS * 3600):
                    return False
            return True
    
    return False
