from .deduplicator import generate_deal_id
from .filters import is_valid_deal
from .scorer import score_deal
from app.utils.logger import logger

def process_raw_deals(raw_deals):
    """
    Filters, deduplicates, and scores a list of raw deals
    """
    processed = []
    
    for d in raw_deals:
        # 1. Filter
        if not is_valid_deal(d):
            continue
            
        # 2. Deduplicate / ID generation
        deal_id = generate_deal_id(d["title"], d["url"])
        
        # 3. Score
        score = score_deal(d)
        
        processed.append({
            "id": deal_id,
            "title": d["title"],
            "url": d["url"],
            "source": d["source"],
            "score": score,
            "category": "electronics" # Default for now
        })
        
    # Sort by score and take top 10
    final_deals = sorted(processed, key=lambda x: x["score"], reverse=True)[:10]
    
    logger.info(f"Processed {len(raw_deals)} raw deals into {len(final_deals)} top deals")
    return final_deals
