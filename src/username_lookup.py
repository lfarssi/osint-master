import requests
from concurrent.futures import ThreadPoolExecutor



PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "GitLab": "https://gitlab.com/{}",
    "Reddit": "https://www.reddit.com/user/{}/",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Twitch": "https://www.twitch.tv/{}",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}


def check_platform(platform_name, url):
    """
    Check if a username exists on one platform.

    Returns a tuple like: ("GitHub", "Found") or ("GitHub", "Not Found")
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)

        if response.status_code == 200:
            return (platform_name, "Found")
        elif response.status_code == 404:
            return (platform_name, "Not Found")
        else:
            return (platform_name, f"Unknown (status {response.status_code})")

    except Exception:
        return (platform_name, "Error (connection failed)")


def get_github_profile(username):
    """
    Get detailed profile info from GitHub's public API.
    No API key needed for basic user info.

    Returns a dictionary with bio, followers, repos, and last activity.
    Returns None if the user doesn't exist or request fails.
    """
    try:
        # GitHub's user API gives us everything
        url = f"https://api.github.com/users/{username}"
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        return {
            "bio": data.get("bio") or "No bio",
            "followers": data.get("followers", 0),
            "following": data.get("following", 0),
            "public_repos": data.get("public_repos", 0),
            "created": data.get("created_at", "Unknown"),
            "last_active": data.get("updated_at", "Unknown"),
        }

    except Exception:
        return None


def lookup(username):
    """
    Check if a username exists on all platforms.
    Also gets detailed GitHub profile info.

    Returns a dictionary with platform results and GitHub profile.
    """
    platform_results = {}

    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks = []
        for name, url_template in PLATFORMS.items():
            url = url_template.format(username)
            tasks.append(pool.submit(check_platform, name, url))

        for task in tasks:
            platform_name, status = task.result()
            platform_results[platform_name] = status

    # Get detailed GitHub profile info
    github_profile = get_github_profile(username)

    return {
        "platforms": platform_results,
        "github_profile": github_profile,
    }
