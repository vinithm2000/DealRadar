from .deduplicator import generate_deal_id
from .filters import is_valid_deal
from .scorer import score_deal
from app.utils.logger import logger

# Category detection keywords
CATEGORY_MAP = {
    "electronics": [
        "mobile", "laptop", "earbuds", "tv", "ssd", "ram", "gpu", "monitor",
        "keyboard", "mouse", "smartphone", "iphone", "samsung", "oneplus",
        "asus", "dell", "hp", "lenovo", "pixel", "macbook", "ipad", "tablet",
        "charger", "power bank", "headphone", "speaker", "smartwatch",
        "camera", "printer", "router", "hard disk", "pendrive"
    ],
    "fashion": [
        "shirt", "shoes", "clothing", "myntra", "ajio", "fashion", "dress",
        "jeans", "jacket", "sneakers", "watch", "sunglasses", "bag", "wallet",
        "kurta", "saree", "nykaa", "cosmetic", "perfume", "grooming"
    ],
    "food": [
        "zomato", "swiggy", "food", "grocery", "blinkit", "bigbasket",
        "instamart", "restaurant", "pizza", "burger", "coffee"
    ],
    "home": [
        "furniture", "mattress", "pillow", "kitchen", "appliance", "fan",
        "ac", "refrigerator", "washing machine", "microwave", "mixer",
        "vacuum", "iron", "purifier"
    ],
    "bank_offers": [
        "hdfc", "sbi", "icici", "axis", "kotak", "bank offer", "card offer"
    ],
}

def detect_category(title):
    """Auto-detect category from deal title"""
    title_lower = title.lower()
    
    best_category = "general"
    best_count = 0
    
    for category, keywords in CATEGORY_MAP.items():
        count = sum(1 for kw in keywords if kw in title_lower)
        if count > best_count:
            best_count = count
            best_category = category
    
    return best_category

def process_raw_deals(raw_deals):
    """
    Filters, deduplicates, and scores a list of raw deals.
    Returns up to 25 top-scoring deals with auto-detected categories.
    """
    seen_ids = set()
    processed = []
    
    for d in raw_deals:
        # 1. Filter (keyword + blacklist + recency)
        if not is_valid_deal(d):
            continue
            
        # 2. Deduplicate by generated ID
        deal_id = generate_deal_id(d["title"], d["url"])
        if deal_id in seen_ids:
            continue
        seen_ids.add(deal_id)
        
        # 3. Score
        score = score_deal(d)
        
        # 4. Auto-detect category
        category = detect_category(d["title"])
        
        processed.append({
            "id": deal_id,
            "title": d["title"],
            "url": d["url"],
            "source": d["source"],
            "score": score,
            "category": category,
            "timestamp": d.get("timestamp")
        })
        
    # Sort by score (highest first), then by timestamp (newest first)
    final_deals = sorted(
        processed, 
        key=lambda x: (x["score"], x.get("timestamp", 0)), 
        reverse=True
    )[:50]
    
    logger.info(f"Processed {len(raw_deals)} raw -> {len(processed)} valid -> {len(final_deals)} top deals")
    
    # Log category breakdown
    cats = {}
    for d in final_deals:
        cats[d['category']] = cats.get(d['category'], 0) + 1
    logger.info(f"Category breakdown: {cats}")
    
    return final_deals
