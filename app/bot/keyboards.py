from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_deal_keyboard(url):
    """
    Returns a keyboard with a 'Buy Now' button
    """
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Now", url=url)]
    ]
    return InlineKeyboardMarkup(keyboard)
