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

def get_latest_deals(limit=10):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deals ORDER BY score DESC, created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

from datetime import datetime
