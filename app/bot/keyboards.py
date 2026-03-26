from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CATEGORY_EMOJIS = {
    "electronics": "📱",
    "fashion": "👗",
    "food": "🍔",
    "home": "🏠",
    "bank_offers": "🏦",
    "general": "📦",
    "all": "🌐",
}

PLAN_CATEGORIES = [
    ("electronics", "Mobiles & Tech"),
    ("fashion", "Fashion"),
    ("food", "Food"),
    ("home", "Home"),
    ("bank_offers", "Bank Offers"),
    ("general", "General"),
]

PLATFORM_LABELS = [
    ("amazon", "Amazon"),
    ("flipkart", "Flipkart"),
    ("other", "Other"),
    ("all", "All"),
]


def build_category_keyboard(current_cats):
    buttons = []
    all_check = "✅" if "all" in current_cats else "⬜"
    buttons.append([InlineKeyboardButton(f"{all_check} 🌐 All Deals", callback_data="cat_all")])

    row = []
    for category, label in PLAN_CATEGORIES:
        emoji = CATEGORY_EMOJIS.get(category, "📦")
        check = "✅" if category in current_cats else "⬜"
        row.append(InlineKeyboardButton(f"{check} {emoji} {label}", callback_data=f"cat_{category}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Done", callback_data="onboard_done")])
    return InlineKeyboardMarkup(buttons)


def build_platform_keyboard(current_platforms):
    buttons = []
    row = []
    for platform, label in PLATFORM_LABELS:
        check = "✅" if platform in current_platforms else "⬜"
        row.append(InlineKeyboardButton(f"{check} {label}", callback_data=f"platform_{platform}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Done", callback_data="onboard_done")])
    return InlineKeyboardMarkup(buttons)


def build_deal_keyboard(deal_id, buy_url):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🛒 Buy Now", url=buy_url),
                InlineKeyboardButton("💾 Save", callback_data=f"save_{deal_id}"),
                InlineKeyboardButton("📤 Share", callback_data=f"share_{deal_id}"),
            ],
            [
                InlineKeyboardButton("👍 Good", callback_data=f"react_good_{deal_id}"),
                InlineKeyboardButton("👎 Skip", callback_data=f"react_bad_{deal_id}"),
                InlineKeyboardButton("⚠️ Expired?", callback_data=f"react_expired_{deal_id}"),
            ],
        ]
    )


def build_settings_keyboard(prefs):
    quiet_label = f"{prefs['quiet_start']:02d}:00-{prefs['quiet_end']:02d}:00"
    digest = "On" if prefs.get("digest_on") else "Off"
    quiet = "On" if prefs.get("quiet_hours_on") else "Off"
    muted = "Muted" if prefs.get("muted") else "Live"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"Digest: {digest}", callback_data="settings_digest"),
                InlineKeyboardButton(f"Mute: {muted}", callback_data="settings_mute"),
            ],
            [
                InlineKeyboardButton("Categories", callback_data="settings_categories"),
                InlineKeyboardButton("Platforms", callback_data="settings_platforms"),
            ],
            [
                InlineKeyboardButton(f"Quiet Hours: {quiet}", callback_data="settings_quiet_toggle"),
                InlineKeyboardButton(quiet_label, callback_data="settings_quiet_window"),
            ],
        ]
    )

