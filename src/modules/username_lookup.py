from core.http_client import DEFAULT_HEADERS
import aiohttp
import asyncio 
from core.http_client import get
import asyncio
import aiohttp
PLATFORMS ={
    "github": "https://api.github.com/users/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "GitLab": "https://gitlab.com/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    # "github": "https://github.com/{}",
    # "twitter": "https://api.twitter.com/users/{username}",
    # "instagram": "https://api.instagram.com/users/{username}",
    # "facebook": "https://api.facebook.com/users/{username}",
    # "linkedin": "https://api.linkedin.com/users/{username}",
    # "youtube": "https://api.youtube.com/users/{username}",
    # "reddit": "https://api.reddit.com/users/{username}",
    # "tiktok": "https://api.tiktok.com/users/{username}",
    # "whatsapp": "https://api.whatsapp.com/users/{username}",
    # "telegram": "https://api.telegram.org/users/{username}",
    # "snapchat": "https://api.snapchat.com/users/{username}",
    # "pinterest": "https://api.pinterest.com/users/{username}",
    # "tumblr": "https://api.tumblr.com/users/{username}",
    # "github": "https://api.github.com/users/{username}",
}

HEADERS={
    "User-Agent": (
        "Mozilla/5.0"
    )
}

async def fetch(session, platform, url):
    try:
        async with session.get(url, timeout=5) as response:
            status=response.status
            if status==200:
                return (platform, "Found")
            elif status==404:
                return (platform, "Not Found")
            else:
                return (platform, f"Error: {status}") 
    except Exception as e:
        return (platform, f"Error: {str(e)}")
async def username_lookup(username):
    tasks=[]
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for platform, url in PLATFORMS.items():
            target=url.format(username)
            tasks.append(fetch(session, platform, target))
        results= await asyncio.gather(*tasks)
        
        
    return dict(results)