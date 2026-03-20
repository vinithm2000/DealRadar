import requests
from app.utils.logger import logger

def fetch_reddit_deals():
    """
    Fetches deals from r/indiandealshunters
    """
    url = "https://www.reddit.com/r/indiandealshunters.json"
    headers = {"User-Agent": "DealRadarBot/1.0"}

    try:
        logger.info(f"Fetching deals from Reddit: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        
        if res.status_code == 429:
            logger.error("Reddit API error: Rate limit exceeded (429). Try increasing user-agent specificity.")
            return []
            
        res.raise_for_status()
        data = res.json()
        
        if "data" not in data or "children" not in data["data"]:
            logger.warning("Reddit API returned unexpected format")
            return []
            
        deals = []
        for post in data.get("data", {}).get("children", []):
            p_data = post.get("data", {})
            if not p_data or "title" not in p_data or "url" not in p_data:
                continue
                
            # Basic normalization
            deals.append({
                "title": p_data["title"],
                "url": p_data["url"],
                "source": "reddit",
                "score": p_data.get("ups", 0),
                "reddit_score": p_data.get("ups", 0),
                "timestamp": p_data.get("created_utc")
            })
        
        logger.info(f"Fetched {len(deals)} deals from Reddit")
        return deals
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching Reddit deals: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching Reddit deals: {e}")
        return []
