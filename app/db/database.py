import sqlite3
import time
import hashlib
from app.utils.config import config
from app.utils.logger import logger
import os

def get_connection():
    return sqlite3.connect(config.DB_PATH)

def init_db():
    """Initialize database tables"""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()

    logger.info(f"Initializing database at {config.DB_PATH}")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deals (
        id TEXT PRIMARY KEY,
        title TEXT,
        url TEXT,
        url_hash TEXT,
        affiliate_url TEXT,
        price REAL,
        original_price REAL,
        discount_pct REAL,
        source TEXT,
        score REAL,
        category TEXT DEFAULT 'general',
        created_at INTEGER,
        posted INTEGER DEFAULT 0
    )
    """)
    
    # Index for fast URL dedup lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_hash ON deals(url_hash)")
    # Index for fast "unposted" queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posted ON deals(posted, created_at)")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        categories TEXT DEFAULT 'all',
        created_at INTEGER
    )
    """)

    conn.commit()
    conn.close()
    
    # Clean old deals on startup
    purge_old_deals()

def _url_hash(url):
    """Generate a hash for URL-based deduplication"""
    normalized = url.strip().lower().split("?")[0]  # Remove query params for dedup
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

def is_deal_exists(url):
    """Check if a deal with this URL already exists in DB"""
    conn = get_connection()
    cursor = conn.cursor()
    h = _url_hash(url)
    cursor.execute("SELECT 1 FROM deals WHERE url_hash = ?", (h,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_deal(deal_data: dict):
    """Save a deal. Returns True if new deal was inserted, False if skipped."""
    url = deal_data.get('url', '')
    h = _url_hash(url)
    
    # Skip if URL already exists (dedup)
    if is_deal_exists(url):
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    deal_timestamp = deal_data.get('timestamp') or int(time.time())
    
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO deals (
            id, title, url, url_hash, affiliate_url, price, original_price, 
            discount_pct, source, score, category, created_at, posted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deal_data['id'], deal_data['title'], url, h,
            deal_data.get('affiliate_url'), deal_data.get('price', 0),
            deal_data.get('original_price', 0), deal_data.get('discount_pct', 0),
            deal_data['source'], deal_data.get('score', 0),
            deal_data.get('category', 'general'), int(deal_timestamp),
            0
        ))
        conn.commit()
        inserted = cursor.rowcount > 0
        return inserted
    except Exception as e:
        logger.error(f"Error saving deal {deal_data.get('id')}: {e}")
        return False
    finally:
        conn.close()

def save_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)", 
                       (user_id, int(time.time())))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving user {user_id}: {e}")
    finally:
        conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_users_by_category(category):
    """Get users subscribed to a specific category or 'all'"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, categories FROM users")
    matched = []
    for row in cursor.fetchall():
        user_id, cats = row
        cat_list = (cats or 'all').split(',')
        if 'all' in cat_list or category in cat_list:
            matched.append(user_id)
    conn.close()
    return matched

def update_user_categories(user_id: int, categories: str):
    """Update a user's category preferences"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET categories = ? WHERE user_id = ?", (categories, user_id))
    conn.commit()
    conn.close()

def get_user_categories(user_id: int):
    """Get a user's subscribed categories"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT categories FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return row[0].split(',')
    return ['all']

def get_latest_deals(limit=10, only_unposted=False):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cutoff = int(time.time()) - (48 * 3600)
    
    if only_unposted:
        cursor.execute(
            "SELECT * FROM deals WHERE posted = 0 AND created_at > ? ORDER BY score DESC LIMIT ?", 
            (cutoff, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM deals WHERE created_at > ? ORDER BY score DESC, created_at DESC LIMIT ?", 
            (cutoff, limit)
        )
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_deal_as_posted(deal_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE deals SET posted = 1 WHERE id = ?", (deal_id,))
    conn.commit()
    conn.close()

def purge_old_deals():
    """Remove deals older than 72 hours"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = int(time.time()) - (72 * 3600)
    cursor.execute("DELETE FROM deals WHERE created_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        logger.info(f"Purged {deleted} old deals from database")

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deals")
    deal_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deals WHERE posted = 1")
    posted_count = cursor.fetchone()[0]
    cutoff = int(time.time()) - (48 * 3600)
    cursor.execute("SELECT COUNT(*) FROM deals WHERE created_at > ?", (cutoff,))
    recent_count = cursor.fetchone()[0]
    conn.close()
    return {
        "users": user_count,
        "total_deals": deal_count,
        "posted_deals": posted_count,
        "recent_deals": recent_count
    }
