# ----------------------------------------------------------
# IP Lookup Module
# ----------------------------------------------------------
# Uses the free ip-api.com API to get information about
# an IP address: location, ISP, timezone, etc.
# ----------------------------------------------------------

from core.http_client import get

API_URL = "http://ip-api.com/json/"


def ip_lookup(ip):
    """
    Look up geolocation and network info for an IP address.

    Returns a dictionary with all the info, or an error message.
    """
    response = get(f"{API_URL}{ip}", timeout=5)

    # If the HTTP request itself failed
    if not response["success"]:
        return {"success": False, "error": response["error"]}

    data = response["data"].json()

    # If the API returned an error (e.g. private IP)
    if data["status"] != "success":
        return {"success": False, "error": "IP lookup failed"}

    # Return the useful fields
    return {
        "success": True,
        "ip": data.get("query"),
        "country": data.get("country"),
        "state": data.get("regionName"),
        "city": data.get("city"),
        "isp": data.get("isp"),
        "org": data.get("org"),
        "asn": data.get("as"),
        "location": f"{data.get('lat')}, {data.get('lon')}",
        "timezone": data.get("timezone"),
        "proxy": data.get("proxy"),
        "hosting": data.get("hosting"),
    }
