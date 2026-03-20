import sqlite3
from app.utils.config import config
from app.utils.logger import logger
import os

def get_connection():
    return sqlite3.connect(config.DB_PATH)

def init_db():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()

    logger.info(f"Initializing database at {config.DB_PATH}")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deals (
        id TEXT PRIMARY KEY,
        title TEXT,
        url TEXT,
        affiliate_url TEXT,
        price REAL,
        original_price REAL,
        discount_pct REAL,
        source TEXT,
        score REAL,
        category TEXT,
        created_at INTEGER,
        posted INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        category TEXT DEFAULT 'all',
        created_at INTEGER
    )
    """)

    conn.commit()
    conn.close()

def save_deal(deal_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO deals (
            id, title, url, affiliate_url, price, original_price, 
            discount_pct, source, score, category, created_at, posted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deal_data['id'], deal_data['title'], deal_data['url'], 
            deal_data.get('affiliate_url'), deal_data.get('price', 0),
            deal_data.get('original_price', 0), deal_data.get('discount_pct', 0),
            deal_data['source'], deal_data.get('score', 0),
            deal_data.get('category', 'all'), deal_data.get('created_at', int(datetime.now().timestamp())),
            0
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving deal {deal_data.get('id')}: {e}")
    finally:
        conn.close()

def save_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)", 
                       (user_id, int(datetime.now().timestamp())))
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

def get_latest_deals(limit=10, only_unposted=False):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if only_unposted:
        cursor.execute("SELECT * FROM deals WHERE posted = 0 ORDER BY score DESC LIMIT ?", (limit,))
    else:
        cursor.execute("SELECT * FROM deals ORDER BY score DESC, created_at DESC LIMIT ?", (limit,))
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_deal_as_posted(deal_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE deals SET posted = 1 WHERE id = ?", (deal_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deals")
    deal_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deals WHERE posted = 1")
    posted_count = cursor.fetchone()[0]
    conn.close()
    return {
        "users": user_count,
        "total_deals": deal_count,
        "posted_deals": posted_count
    }

from datetime import datetime
