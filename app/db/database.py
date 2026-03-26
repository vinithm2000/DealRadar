import hashlib
import os
import sqlite3
import time

from app.utils.config import config
from app.utils.logger import logger

DEFAULT_CATEGORIES = "all"
DEFAULT_PLATFORMS = "all"
DEFAULT_QUIET_START = 23
DEFAULT_QUIET_END = 8
MAX_WISHLIST_ITEMS = 20


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()
    logger.info(f"Initializing database at {config.DB_PATH}")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            url_hash TEXT,
            affiliate_url TEXT,
            price REAL DEFAULT 0,
            original_price REAL DEFAULT 0,
            discount_pct REAL DEFAULT 0,
            source TEXT,
            score REAL DEFAULT 0,
            category TEXT DEFAULT 'general',
            platform TEXT DEFAULT 'unknown',
            expires_at INTEGER,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at INTEGER,
            posted INTEGER DEFAULT 0
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            categories TEXT DEFAULT 'all',
            platforms TEXT DEFAULT 'all',
            digest_on INTEGER DEFAULT 1,
            muted INTEGER DEFAULT 0,
            quiet_hours_on INTEGER DEFAULT 0,
            quiet_start INTEGER DEFAULT 23,
            quiet_end INTEGER DEFAULT 8,
            onboarding_done INTEGER DEFAULT 0,
            timezone TEXT DEFAULT 'Asia/Kolkata',
            created_at INTEGER,
            last_seen_at INTEGER
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS wishlist (
            user_id INTEGER NOT NULL,
            deal_id TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, deal_id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS deal_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            deal_id TEXT NOT NULL,
            action TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            UNIQUE(user_id, deal_id, action)
        )
        """
    )

    migrations = [
        ("deals", "url_hash", "ALTER TABLE deals ADD COLUMN url_hash TEXT"),
        ("deals", "category", "ALTER TABLE deals ADD COLUMN category TEXT DEFAULT 'general'"),
        ("deals", "platform", "ALTER TABLE deals ADD COLUMN platform TEXT DEFAULT 'unknown'"),
        ("deals", "expires_at", "ALTER TABLE deals ADD COLUMN expires_at INTEGER"),
        ("deals", "image_url", "ALTER TABLE deals ADD COLUMN image_url TEXT"),
        ("deals", "is_active", "ALTER TABLE deals ADD COLUMN is_active INTEGER DEFAULT 1"),
        ("users", "categories", "ALTER TABLE users ADD COLUMN categories TEXT DEFAULT 'all'"),
        ("users", "platforms", "ALTER TABLE users ADD COLUMN platforms TEXT DEFAULT 'all'"),
        ("users", "digest_on", "ALTER TABLE users ADD COLUMN digest_on INTEGER DEFAULT 1"),
        ("users", "muted", "ALTER TABLE users ADD COLUMN muted INTEGER DEFAULT 0"),
        ("users", "quiet_hours_on", "ALTER TABLE users ADD COLUMN quiet_hours_on INTEGER DEFAULT 0"),
        ("users", "quiet_start", "ALTER TABLE users ADD COLUMN quiet_start INTEGER DEFAULT 23"),
        ("users", "quiet_end", "ALTER TABLE users ADD COLUMN quiet_end INTEGER DEFAULT 8"),
        ("users", "onboarding_done", "ALTER TABLE users ADD COLUMN onboarding_done INTEGER DEFAULT 0"),
        ("users", "timezone", "ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'Asia/Kolkata'"),
        ("users", "last_seen_at", "ALTER TABLE users ADD COLUMN last_seen_at INTEGER"),
    ]

    for table, column, sql in migrations:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(sql)
            logger.info(f"Migration: Added {table}.{column}")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_url_hash ON deals(url_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_active_posted ON deals(is_active, posted, created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_search ON deals(is_active, category, platform)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wishlist_user ON wishlist(user_id, created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_deal ON deal_interactions(deal_id, action)")

    conn.commit()
    conn.close()

    purge_old_deals()
    expire_deals()


def _now():
    return int(time.time())


def _url_hash(url: str):
    normalized = (url or "").strip().lower().split("?")[0]
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def infer_platform(url: str):
    normalized = (url or "").lower()
    if "amazon." in normalized or "amzn." in normalized:
        return "amazon"
    if "flipkart" in normalized or "fkrt." in normalized:
        return "flipkart"
    return "other"


def ensure_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    now = _now()
    cursor.execute(
        """
        INSERT INTO users (
            user_id, categories, platforms, digest_on, muted, quiet_hours_on,
            quiet_start, quiet_end, onboarding_done, timezone, created_at, last_seen_at
        ) VALUES (?, ?, ?, 1, 0, 0, ?, ?, 0, 'Asia/Kolkata', ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_seen_at = excluded.last_seen_at
        """,
        (user_id, DEFAULT_CATEGORIES, DEFAULT_PLATFORMS, DEFAULT_QUIET_START, DEFAULT_QUIET_END, now, now),
    )
    conn.commit()
    conn.close()


def save_user(user_id: int):
    ensure_user(user_id)


def is_deal_exists(url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM deals WHERE url_hash = ?", (_url_hash(url),))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def save_deal(deal_data: dict):
    url = deal_data.get("url", "")
    url_hash = _url_hash(url)
    if is_deal_exists(url):
        return False

    conn = get_connection()
    cursor = conn.cursor()
    try:
        created_at = int(deal_data.get("timestamp") or _now())
        cursor.execute(
            """
            INSERT OR IGNORE INTO deals (
                id, title, url, url_hash, affiliate_url, price, original_price,
                discount_pct, source, score, category, platform, expires_at,
                image_url, is_active, created_at, posted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deal_data["id"],
                deal_data["title"],
                url,
                url_hash,
                deal_data.get("affiliate_url"),
                float(deal_data.get("price") or 0),
                float(deal_data.get("original_price") or 0),
                float(deal_data.get("discount_pct") or 0),
                deal_data.get("source", ""),
                float(deal_data.get("score") or 0),
                deal_data.get("category", "general"),
                deal_data.get("platform") or infer_platform(url),
                deal_data.get("expires_at"),
                deal_data.get("image_url"),
                1,
                created_at,
                0,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as exc:
        logger.error(f"Error saving deal {deal_data.get('id')}: {exc}")
        return False
    finally:
        conn.close()


def get_deal_by_id(deal_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_deals(limit=10, only_unposted=False, active_only=True):
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = _now() - (72 * 3600)
    clauses = ["created_at > ?"]
    params = [cutoff]
    if active_only:
        clauses.append("is_active = 1")
    if only_unposted:
        clauses.append("posted = 0")
    where_sql = " AND ".join(clauses)
    cursor.execute(
        f"SELECT * FROM deals WHERE {where_sql} ORDER BY score DESC, created_at DESC LIMIT ?",
        (*params, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_deals(query: str, limit=3):
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{query.strip()}%"
    cursor.execute(
        """
        SELECT * FROM deals
        WHERE is_active = 1 AND title LIKE ?
        ORDER BY score DESC, created_at DESC
        LIMIT ?
        """,
        (like, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_todays_top_deals(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = _now() - (24 * 3600)
    cursor.execute(
        """
        SELECT d.*, COALESCE(COUNT(i.id), 0) AS interaction_count
        FROM deals d
        LEFT JOIN deal_interactions i ON i.deal_id = d.id
        WHERE d.is_active = 1 AND d.created_at > ?
        GROUP BY d.id
        ORDER BY interaction_count DESC, d.score DESC, d.created_at DESC
        LIMIT ?
        """,
        (cutoff, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


def get_user_preferences(user_id: int):
    ensure_user(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    prefs = dict(row)
    prefs["category_list"] = _split_csv(prefs.get("categories"), DEFAULT_CATEGORIES)
    prefs["platform_list"] = _split_csv(prefs.get("platforms"), DEFAULT_PLATFORMS)
    return prefs


def _split_csv(value, default_value):
    raw = (value or default_value).strip()
    return [part for part in raw.split(",") if part] or [default_value]


def get_user_categories(user_id: int):
    return get_user_preferences(user_id)["category_list"]


def get_user_platforms(user_id: int):
    return get_user_preferences(user_id)["platform_list"]


def update_user_categories(user_id: int, categories: str):
    ensure_user(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET categories = ?, onboarding_done = 1 WHERE user_id = ?", (categories, user_id))
    conn.commit()
    conn.close()


def update_user_platforms(user_id: int, platforms: str):
    ensure_user(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET platforms = ?, onboarding_done = 1 WHERE user_id = ?", (platforms, user_id))
    conn.commit()
    conn.close()


def update_user_settings(user_id: int, **fields):
    ensure_user(user_id)
    allowed = {
        "digest_on",
        "muted",
        "quiet_hours_on",
        "quiet_start",
        "quiet_end",
        "categories",
        "platforms",
        "onboarding_done",
        "timezone",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return
    assignments = ", ".join(f"{column} = ?" for column in updates.keys())
    params = list(updates.values()) + [user_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {assignments} WHERE user_id = ?", params)
    conn.commit()
    conn.close()


def get_matching_users_for_deal(deal: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = []
    for row in cursor.fetchall():
        prefs = dict(row)
        if not deal_matches_preferences(deal, prefs):
            continue
        users.append(prefs)
    conn.close()
    return users


def deal_matches_preferences(deal: dict, prefs: dict):
    if prefs.get("muted"):
        return False

    categories = _split_csv(prefs.get("categories"), DEFAULT_CATEGORIES)
    platforms = _split_csv(prefs.get("platforms"), DEFAULT_PLATFORMS)
    deal_category = deal.get("category", "general")
    deal_platform = deal.get("platform") or infer_platform(deal.get("url", ""))

    category_ok = "all" in categories or deal_category in categories
    platform_ok = "all" in platforms or deal_platform in platforms
    quiet_ok = not user_in_quiet_hours(prefs)
    return category_ok and platform_ok and quiet_ok


def user_in_quiet_hours(prefs: dict, current_hour=None):
    if not prefs.get("quiet_hours_on"):
        return False
    current_hour = _local_hour(current_hour)
    start = int(prefs.get("quiet_start", DEFAULT_QUIET_START))
    end = int(prefs.get("quiet_end", DEFAULT_QUIET_END))
    if start == end:
        return True
    if start < end:
        return start <= current_hour < end
    return current_hour >= start or current_hour < end


def _local_hour(epoch=None):
    return time.localtime(epoch or time.time()).tm_hour


def add_to_wishlist(user_id: int, deal_id: str):
    ensure_user(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM wishlist WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0] >= MAX_WISHLIST_ITEMS:
        conn.close()
        return False, "Wishlist is full. Limit is 20 deals."
    try:
        cursor.execute(
            "INSERT INTO wishlist (user_id, deal_id, created_at) VALUES (?, ?, ?)",
            (user_id, deal_id, _now()),
        )
        conn.commit()
        return True, "Saved to wishlist."
    except sqlite3.IntegrityError:
        return False, "This deal is already in your wishlist."
    finally:
        conn.close()


def remove_from_wishlist(user_id: int, deal_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlist WHERE user_id = ? AND deal_id = ?", (user_id, deal_id))
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed


def clear_wishlist(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlist WHERE user_id = ?", (user_id,))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count


def get_wishlist(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT d.* FROM wishlist w
        JOIN deals d ON d.id = w.deal_id
        WHERE w.user_id = ?
        ORDER BY w.created_at DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_interaction(user_id: int, deal_id: str, action: str):
    ensure_user(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO deal_interactions (user_id, deal_id, action, created_at) VALUES (?, ?, ?, ?)",
            (user_id, deal_id, action, _now()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_deal_interaction_summary(deal_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT action, COUNT(*) AS count
        FROM deal_interactions
        WHERE deal_id = ?
        GROUP BY action
        """,
        (deal_id,),
    )
    counts = {row["action"]: row["count"] for row in cursor.fetchall()}
    conn.close()
    return counts


def mark_deal_as_posted(deal_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE deals SET posted = 1 WHERE id = ?", (deal_id,))
    conn.commit()
    conn.close()


def mark_deal_inactive(deal_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE deals SET is_active = 0 WHERE id = ?", (deal_id,))
    cursor.execute("DELETE FROM wishlist WHERE deal_id = ?", (deal_id,))
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed


def expire_deals():
    conn = get_connection()
    cursor = conn.cursor()
    now = _now()
    cursor.execute("UPDATE deals SET is_active = 0 WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,))
    expired = cursor.rowcount
    if expired:
        cursor.execute("DELETE FROM wishlist WHERE deal_id IN (SELECT id FROM deals WHERE is_active = 0)")
    conn.commit()
    conn.close()
    if expired:
        logger.info(f"Marked {expired} expired deals inactive")
    return expired


def purge_old_deals():
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = _now() - (72 * 3600)
    cursor.execute("DELETE FROM wishlist WHERE deal_id IN (SELECT id FROM deals WHERE created_at < ?)", (cutoff,))
    cursor.execute("DELETE FROM deals WHERE created_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted:
        logger.info(f"Purged {deleted} old deals from database")


def clear_all_deals():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM deals")
    count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM wishlist")
    cursor.execute("DELETE FROM deal_interactions")
    cursor.execute("DELETE FROM deals")
    conn.commit()
    conn.close()
    logger.info(f"Cleared all {count} deals from database")
    return count


def create_manual_deal(title, price, original_price, url, platform, category, hours_valid):
    now = _now()
    deal_id = hashlib.sha256(f"{title}|{url}|{now}".encode()).hexdigest()[:16]
    discount_pct = 0
    if original_price and float(original_price) > 0 and float(price) >= 0:
        discount_pct = round((1 - (float(price) / float(original_price))) * 100, 2)
    payload = {
        "id": deal_id,
        "title": title.strip(),
        "url": url.strip(),
        "affiliate_url": url.strip(),
        "price": float(price),
        "original_price": float(original_price),
        "discount_pct": discount_pct,
        "source": "manual_admin",
        "score": max(60, discount_pct + 40),
        "category": category.strip().lower(),
        "platform": platform.strip().lower(),
        "expires_at": now + (int(hours_valid) * 3600),
        "timestamp": now,
    }
    inserted = save_deal(payload)
    return payload if inserted else None


def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    now = _now()
    day_cutoff = now - (24 * 3600)
    week_cutoff = now - (7 * 24 * 3600)

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_seen_at > ?", (day_cutoff,))
    active_today = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_seen_at > ?", (week_cutoff,))
    active_7d = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deals")
    total_deals = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deals WHERE is_active = 1")
    active_deals = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM wishlist")
    wishlist_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deal_interactions WHERE action = 'buy'")
    buy_clicks = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT d.title, COUNT(i.id) AS clicks
        FROM deal_interactions i
        JOIN deals d ON d.id = i.deal_id
        WHERE i.action = 'buy'
        GROUP BY i.deal_id
        ORDER BY clicks DESC
        LIMIT 3
        """
    )
    top_clicked = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {
        "users": users,
        "active_today": active_today,
        "active_7d": active_7d,
        "total_deals": total_deals,
        "active_deals": active_deals,
        "wishlist_count": wishlist_count,
        "buy_clicks": buy_clicks,
        "top_clicked": top_clicked,
    }
