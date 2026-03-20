import requests
import time
from app.utils.logger import logger

# Active Indian deals subreddits
SUBREDDITS = [
    "IndianGaming",
    "indiandeals", 
    "dealsforindia",
]

def fetch_reddit_deals():
    """
    Fetches recent deals from multiple Indian deal subreddits
    """
    headers = {"User-Agent": "DealRadarBot/2.0 (by /u/dealradar)"}
    all_deals = []
    now = time.time()

    for subreddit in SUBREDDITS:
        try:
            # Fetch "new" posts (most recent first)
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
            logger.info(f"Fetching deals from Reddit: r/{subreddit}")
            res = requests.get(url, headers=headers, timeout=15)
            
            if res.status_code == 429:
                logger.warning(f"Reddit rate limit on r/{subreddit}, skipping")
                continue
            if res.status_code == 403:
                logger.warning(f"Reddit r/{subreddit} is private or banned, skipping")
                continue
                
            res.raise_for_status()
            data = res.json()
            
            posts = data.get("data", {}).get("children", [])
            
            for post in posts:
                p = post.get("data", {})
                if not p or not p.get("title") or not p.get("url"):
                    continue
                
                # Skip stickied/pinned posts (often old rules/guides)
                if p.get("stickied", False):
                    continue
                    
                created_utc = p.get("created_utc", 0)
                
                # Skip posts older than 48 hours
                age_hours = (now - created_utc) / 3600
                if age_hours > 48:
                    continue
                
                all_deals.append({
                    "title": p["title"],
                    "url": p["url"],
                    "source": f"reddit_{subreddit}",
                    "reddit_score": p.get("ups", 0),
                    "timestamp": created_utc
                })
            
            logger.info(f"Fetched {len(posts)} posts from r/{subreddit}, kept recent ones")
            
            # Be polite to Reddit API
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching r/{subreddit}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching r/{subreddit}: {e}")
    
    logger.info(f"Total recent Reddit deals: {len(all_deals)}")
    return all_deals
