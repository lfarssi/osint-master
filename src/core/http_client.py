# ----------------------------------------------------------
# HTTP Client
# ----------------------------------------------------------
# A simple wrapper around the requests library.
# All HTTP GET requests in this project go through here
# so we have one place to set headers and handle errors.
# ----------------------------------------------------------

import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}


def get(url, timeout=5):
    """
    Send a GET request and return a simple result dictionary.

    Returns:
        On success: {"success": True, "status_code": 200, "data": <Response>}
        On failure: {"success": False, "error": "error message"}
    """
    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout
        )
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response
        }
    except requests.RequestException as error:
        return {
            "success": False,
            "error": str(error)
        }