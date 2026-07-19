# ----------------------------------------------------------
# Input Validators
# ----------------------------------------------------------
# Simple functions that check if user input is valid
# before we send it to any API or DNS lookup.
# ----------------------------------------------------------

import ipaddress
import re


def validate_ip(ip):
    """Check if the string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_domain(domain):
    """Check if the string looks like a valid domain name."""
    pattern = r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
    return re.match(pattern, domain) is not None


def validate_username(username):
    """Check if the username only contains safe characters (3-30 chars)."""
    pattern = r"^[a-zA-Z0-9._-]{3,30}$"
    return re.match(pattern, username) is not None