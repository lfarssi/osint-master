from core.http_client import get
PLATFORMS ={
    "github": "https://api.github.com/users/{username}",
    "twitter": "https://api.twitter.com/users/{username}",
    "instagram": "https://api.instagram.com/users/{username}",
    "facebook": "https://api.facebook.com/users/{username}",
    "linkedin": "https://api.linkedin.com/users/{username}",
    "youtube": "https://api.youtube.com/users/{username}",
    "reddit": "https://api.reddit.com/users/{username}",
    "tiktok": "https://api.tiktok.com/users/{username}",
    "whatsapp": "https://api.whatsapp.com/users/{username}",
    "telegram": "https://api.telegram.org/users/{username}",
    "snapchat": "https://api.snapchat.com/users/{username}",
    "pinterest": "https://api.pinterest.com/users/{username}",
    "tumblr": "https://api.tumblr.com/users/{username}",
    "github": "https://api.github.com/users/{username}",
}


def username_lookup(username):
    response = get(f"")