import time

# Merchant domains that pay EarnKaro commissions
MERCHANT_DOMAINS = [
    "amazon.in", "amazon.com", "amzn.to", "amzn.in",
    "flipkart.com", "dl.flipkart.com", "fkrt.it",
    "myntra.com", "ajio.com", "meesho.com", "nykaa.com",
    "croma.com", "jiomart.com", "tatacliq.com",
]

def score_deal(deal):
    """
    Calculates a quality score for a deal.
    Higher scores appear first in /deals and get broadcast first.
    """
    score = 50  # Base score
    title = deal.get("title", "").lower()
    url = deal.get("url", "").lower()
    
    # === MERCHANT URL BONUS (critical for EarnKaro revenue) ===
    for merchant in MERCHANT_DOMAINS:
        if merchant in url:
            score += 30  # Strong boost — these earn commission
            break
    
    # === Discount indicators ===
    if any(w in title for w in ["off", "%", "₹", "rs", "flat"]):
        score += 20
    if any(w in title for w in ["lowest", "price drop", "loot", "steal", "hurry"]):
        score += 15
    if any(w in title for w in ["free", "cashback", "coupon"]):
        score += 10
    
    # === Bank card offers get a bonus ===
    if any(w in title for w in ["hdfc", "sbi", "icici", "axis", "kotak", "bank", "card offer"]):
        score += 20
    
    # === Recency bonus ===
    if deal.get("timestamp"):
        age_hours = (time.time() - deal["timestamp"]) / 3600
        if age_hours < 6:
            score += 20
        elif age_hours < 12:
            score += 15
        elif age_hours < 24:
            score += 5
        elif age_hours > 48:
            score -= 10
    
    # === Reddit upvotes ===
    if deal.get("reddit_score"):
        score += min(deal["reddit_score"], 100) * 0.3
    
    # === Source bonuses ===
    source = deal.get("source", "")
    if "desidime_merchant" in source or "amazon" in source or "flipkart" in source:
        score += 15  # Direct merchant sources
    elif "desidime" in source:
        score += 10
    elif "feed_" in source:
        score += 5
        
    return score
