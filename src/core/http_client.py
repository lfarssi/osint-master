import requests

DEFAULT_HEADERS={
    "User-Agent":(
        "Mozilla/5.0 (X11; Linux x86_64)"
    )
}

def get(url, timeout=5):
    try:
        response=requests.get(url,headers=DEFAULT_HEADERS, timeout=timeout )
        return {
            "success":True,
            "status_code":response.status_code,
            "data":response
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error":str(e)
        }