import requests
import time
from app.utils.logger import logger

# Active Indian deals subreddits — more sources
SUBREDDITS = [
    "IndianGaming",
    "indiandeals", 
    "dealsforindia",
    "india",
    "mobiledeals",
]

def fetch_reddit_deals():
    """
    Fetches recent deals from multiple Indian subreddits.
    Fetches /new posts and searches for deal flairs.
    """
    headers = {"User-Agent": "DealRadarBot/2.0 (contact: techverzion@gmail.com)"}
    all_deals = []
    now = time.time()

    for subreddit in SUBREDDITS:
        try:
            # Fetch "new" posts (most recent first)
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=50"
            logger.info(f"Reddit: Fetching r/{subreddit}")
            res = requests.get(url, headers=headers, timeout=15)
            
            if res.status_code == 429:
                logger.warning(f"Reddit: Rate limit on r/{subreddit}")
                continue
            if res.status_code in (403, 404):
                logger.warning(f"Reddit: r/{subreddit} unavailable ({res.status_code})")
                continue
                
            res.raise_for_status()
            data = res.json()
            
            posts = data.get("data", {}).get("children", [])
            kept = 0
            
            for post in posts:
                p = post.get("data", {})
                if not p or not p.get("title"):
                    continue
                
                # Skip stickied/pinned posts
                if p.get("stickied", False):
                    continue
                
                # Skip self-posts with no external URL (just discussions)
                post_url = p.get("url", "")
                if p.get("is_self", False):
                    # For self posts, use the Reddit comments URL instead
                    post_url = f"https://www.reddit.com{p.get('permalink', '')}"
                    
                created_utc = p.get("created_utc", 0)
                
                # Skip posts older than 72 hours
                age_hours = (now - created_utc) / 3600
                if age_hours > 72:
                    continue
                
                all_deals.append({
                    "title": p["title"],
                    "url": post_url,
                    "source": f"reddit_{subreddit}",
                    "reddit_score": p.get("ups", 0),
                    "timestamp": created_utc
                })
                kept += 1
            
            logger.info(f"Reddit: Kept {kept} recent from r/{subreddit} (total {len(posts)} posts)")
            
            # Be polite to Reddit API
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Reddit: Network error r/{subreddit}: {e}")
        except Exception as e:
            logger.error(f"Reddit: Error r/{subreddit}: {e}")
    
    logger.info(f"Reddit: Total {len(all_deals)} recent deals")
    return all_deals
