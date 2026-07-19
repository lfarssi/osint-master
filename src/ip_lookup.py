# -------------------------------------------------------
# IP Lookup Module
# -------------------------------------------------------
# Uses the free ip-api.com API to get info about an IP:
#   - Country, city, ISP, ASN
#   - Whether the IP is a proxy/VPN or hosting provider
#
# No API key needed. Free for non-commercial use.
# Docs: https://ip-api.com/docs/api:json
# -------------------------------------------------------

import requests


def lookup(ip_address):
    """
    Look up an IP address and return its info as a dictionary.

    Example:
        result = lookup("8.8.8.8")
        print(result["country"])  # "United States"
    """
    # ip-api.com gives us everything we need in one call
    url = f"http://ip-api.com/json/{ip_address}"
    params = {
        "fields": "status,message,query,country,regionName,city,isp,org,as,proxy,hosting"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception as error:
        return {"success": False, "error": str(error)}

    # ip-api returns status "fail" for invalid or private IPs
    if data.get("status") != "success":
        return {"success": False, "error": data.get("message", "Lookup failed")}

    # Check for abuse indicators using the proxy/hosting flags
    # proxy = True means VPN/proxy, hosting = True means data center
    known_issues = []
    if data.get("proxy"):
        known_issues.append("IP is associated with a proxy or VPN")
    if data.get("hosting"):
        known_issues.append("IP belongs to a hosting/data center")
    if not known_issues:
        known_issues.append("No reported abuse")

    return {
        "success": True,
        "ip": data.get("query"),
        "country": data.get("country"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "isp": data.get("isp"),
        "org": data.get("org"),
        "asn": data.get("as"),
        "known_issues": known_issues,
    }
