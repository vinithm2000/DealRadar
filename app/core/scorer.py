def score_deal(deal):
    """
    Calculates a quality score for a deal
    """
    score = 50 # Base score
    
    title = deal["title"].lower()
    
    # Bonus for common discount indicators
    if "off" in title or "%" in title:
        score += 20
        
    if "lowest" in title or "price drop" in title:
        score += 15
        
    # Recency Bonus (e.g., posted in last 12 hours)
    import time
    if deal.get("timestamp"):
        age_hours = (time.time() - deal["timestamp"]) / 3600
        if age_hours < 12:
            score += 15
        elif age_hours > 24:
            score -= 10 # Slight penalty for older deals
            
    # Reddit upvotes bonus
    if deal.get("reddit_score"):
        score += min(deal["reddit_score"], 100) * 0.3
        
    # Source bonus
    if "desidime" in deal.get("source", ""):
        score += 10
        
    return score
