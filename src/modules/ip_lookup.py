import requests 

API_URL = "http://ip-api.com/json/"


def ip_lookup(ip):
    try:
        response = requests.get(f"{API_URL}{ip}", timeout=5)
        if response.status_code !=200:
            return {"success": False, "error": "Failed to fetch data" }
        data= response.json()
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
    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }
