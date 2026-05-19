from core.http_client import get
API_URL = "http://ip-api.com/json/"


def ip_lookup(ip):
    response = get(f"{API_URL}{ip}", timeout=5)
    if not response["success"]:
        return {"success": False, "error": response["error"] }
    data= response["data"].json()
    if data["status"] != "success":
        return {
            "success": False,
            "error": "Invalid IP lookup"
        }
    return {
        "success": True,
        "country": data.get("country"),
        "state": data.get("regionName"),
        "city": data.get("city"),
        "isp": data.get("isp"),
        "proxy": data.get("proxy"),
        "hosting": data.get("hosting"),
        "location": f"{data.get('lat')}, {data.get('lon')}",
        "timezone": data.get("timezone"),
        "query": data.get("query"),
        "asn": data.get("as"),
        "org": data.get("org")
    }
