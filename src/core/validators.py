import ipaddress
import re

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
def validate_domain(domain):
    pattern =""
    return re.match(pattern, domain) is not None

def validate_username(username):
    pattern =r"^[a-zA-Z0-9._-]{3,30}$"
    return re.match(pattern, username) is not None
    