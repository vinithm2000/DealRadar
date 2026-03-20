import hashlib

def generate_deal_id(title, url):
    """
    Generates a unique SHA1 hash for a deal based on title and URL
    """
    combined = f"{title.lower().strip()}{url.strip()}"
    return hashlib.sha1(combined.encode()).hexdigest()
