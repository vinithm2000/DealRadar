from .deduplicator import generate_deal_id
from .filters import is_valid_deal
from .scorer import score_deal
from app.utils.logger import logger

def process_raw_deals(raw_deals):
    """
    Filters, deduplicates, and scores a list of raw deals.
    Returns up to 25 top-scoring deals.
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
        
        processed.append({
            "id": deal_id,
            "title": d["title"],
            "url": d["url"],
            "source": d["source"],
            "score": score,
            "category": "electronics",
            "timestamp": d.get("timestamp")
        })
        
    # Sort by score (highest first), then by timestamp (newest first)
    final_deals = sorted(
        processed, 
        key=lambda x: (x["score"], x.get("timestamp", 0)), 
        reverse=True
    )[:25]
    
    logger.info(f"Processed {len(raw_deals)} raw deals -> {len(processed)} valid -> {len(final_deals)} top deals")
    return final_deals
