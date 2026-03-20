from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Deal:
    id: str
    title: str
    url: str
    price: float
    original_price: float
    discount_pct: float
    source: str
    score: float
    category: str = 'all'
    affiliate_url: Optional[str] = None
    created_at: int = int(datetime.now().timestamp())
    posted: int = 0
