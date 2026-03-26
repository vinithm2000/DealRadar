import html
import time

from app.bot.keyboards import CATEGORY_EMOJIS
from app.db.database import get_deal_interaction_summary


def deal_heat_badge(deal):
    discount = float(deal.get("discount_pct") or 0)
    score = float(deal.get("score") or 0)
    if discount >= 50 or score >= 100:
        return "🔥 HOT"
    if discount >= 25 or score >= 80:
        return "✅ Good"
    return "👍 OK"


def format_currency(value):
    if value in (None, "", 0, 0.0):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if amount.is_integer():
        return f"₹{int(amount):,}"
    return f"₹{amount:,.2f}"


def format_expiry(expires_at):
    if not expires_at:
        return "No expiry listed"
    remaining = int(expires_at - time.time())
    if remaining <= 0:
        return "Expired"
    hours, rem = divmod(remaining, 3600)
    minutes = rem // 60
    if hours:
        return f"Ends in {hours}h {minutes}m"
    return f"Ends in {minutes}m"


def build_deal_message(deal, compact=False):
    badge = deal_heat_badge(deal)
    platform = (deal.get("platform") or "unknown").capitalize()
    category = deal.get("category", "general")
    category_emoji = CATEGORY_EMOJIS.get(category, "📦")
    title = html.escape(deal.get("title", "Untitled deal"))
    current_price = format_currency(deal.get("price"))
    original_price = format_currency(deal.get("original_price"))
    discount = int(float(deal.get("discount_pct") or 0))
    savings = None
    if deal.get("price") and deal.get("original_price"):
        savings = float(deal["original_price"]) - float(deal["price"])

    lines = [f"<b>{badge}</b> · {html.escape(platform)}", "", f"<b>{title}</b>"]
    price_line = []
    if current_price:
        price_line.append(current_price)
    if original_price and original_price != current_price:
        price_line.append(f"<s>{original_price}</s>")
    if discount > 0:
        price_line.append(f"{discount}% OFF")
    if price_line:
        lines.append(" ".join(price_line))
    if savings and savings > 0:
        lines.append(f"💰 Save {format_currency(savings)}")
    lines.append(f"{category_emoji} {html.escape(category.replace('_', ' ').title())}")
    lines.append(f"⏰ {format_expiry(deal.get('expires_at'))}")

    if compact:
        return "\n".join(line for line in lines if line)

    interaction_counts = get_deal_interaction_summary(deal["id"])
    counts = []
    if interaction_counts.get("good"):
        counts.append(f"👍 {interaction_counts['good']}")
    if interaction_counts.get("save"):
        counts.append(f"💾 {interaction_counts['save']}")
    if interaction_counts.get("expired"):
        counts.append(f"⚠️ {interaction_counts['expired']}")
    if counts:
        lines.append(" · ".join(counts))

    return "\n".join(line for line in lines if line)

