import requests
import time
from app.utils.logger import logger

# Active Indian deals subreddits
SUBREDDITS = [
    "IndianGaming",
    "indiandeals", 
    "dealsforindia",
    "mobiledeals",
]

def fetch_reddit_deals():
    """
    Fetches recent deals from Indian deal subreddits.
    Robust error handling - never crashes the pipeline.
    """
    headers = {
        "User-Agent": "DealRadarBot/2.0 (contact: techverzion@gmail.com)",
        "Accept": "application/json",
    }
    all_deals = []
    now = time.time()

    for subreddit in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25&raw_json=1"
            logger.info(f"Reddit: Fetching r/{subreddit}")
            
            res = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if res.status_code == 429:
                logger.warning(f"Reddit: Rate limited on r/{subreddit}, waiting 5s")
                time.sleep(5)
                continue
            if res.status_code in (403, 404, 451):
                logger.warning(f"Reddit: r/{subreddit} unavailable ({res.status_code})")
                continue
            if res.status_code != 200:
                logger.warning(f"Reddit: r/{subreddit} returned {res.status_code}")
                continue
                
            data = res.json()
            posts = data.get("data", {}).get("children", [])
            kept = 0
            
            for post in posts:
                p = post.get("data", {})
                if not p or not p.get("title"):
                    continue
                
                # Skip stickied posts
                if p.get("stickied", False):
                    continue
                
                # Get the URL - for self posts, use the Reddit link
                post_url = p.get("url", "")
                if p.get("is_self", False) or "reddit.com" in post_url:
                    post_url = f"https://www.reddit.com{p.get('permalink', '')}"
                    
                created_utc = p.get("created_utc", 0)
                
                # Skip old posts
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
            
            logger.info(f"Reddit: r/{subreddit} - kept {kept} recent (from {len(posts)} posts)")
            
            # Polite delay between subreddits
            time.sleep(3)
            
        except requests.exceptions.Timeout:
            logger.warning(f"Reddit: Timeout on r/{subreddit}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Reddit: Connection error on r/{subreddit}")
        except Exception as e:
            logger.error(f"Reddit: Unexpected error r/{subreddit}: {e}")
    
    logger.info(f"Reddit: Total {len(all_deals)} recent deals from {len(SUBREDDITS)} subs")
    return all_deals
