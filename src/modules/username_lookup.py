# ----------------------------------------------------------
# Username Lookup Module
# ----------------------------------------------------------
# Checks if a username exists on popular platforms by
# sending HTTP requests and checking the response status.
#
# Uses async (aiohttp) to check all platforms at once
# instead of one by one, which is much faster.
# ----------------------------------------------------------

import aiohttp
import asyncio

# Each platform has a URL where we can check if a user exists.
# The {} gets replaced with the actual username.
PLATFORMS = {
    "GitHub": "https://api.github.com/users/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "GitLab": "https://gitlab.com/{}",
    "Pinterest": "https://www.pinterest.com/{}",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}


async def check_platform(session, platform, url):
    """
    Check if a username exists on one platform.

    Returns a tuple like ("GitHub", "Found") or ("GitHub", "Not Found").
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                return (platform, "Found")
            elif response.status == 404:
                return (platform, "Not Found")
            else:
                return (platform, f"Unknown (status {response.status})")
    except Exception:
        return (platform, "Error (connection failed)")


async def username_lookup(username):
    """
    Check all platforms for a username. Returns a dictionary like:
    {"GitHub": "Found", "Reddit": "Not Found", ...}
    """
    tasks = []

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for platform, url_template in PLATFORMS.items():
            url = url_template.format(username)
            tasks.append(check_platform(session, platform, url))

        results = await asyncio.gather(*tasks)

    return dict(results)