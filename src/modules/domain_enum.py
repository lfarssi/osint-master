# ----------------------------------------------------------
# Domain Enumeration Module
# ----------------------------------------------------------
# This module does three things for a domain:
#
# 1. DNS Resolution   - looks up A, MX, NS, CNAME records
# 2. Subdomain Enum   - finds subdomains using a wordlist
# 3. Takeover Check   - checks if a subdomain might be
#                        vulnerable to takeover
#
# Subdomain enumeration uses async (aiodns) to check many
# subdomains at the same time, which is much faster.
# ----------------------------------------------------------

import socket
import ssl
import dns.resolver
import asyncio
import aiodns
import requests
from pathlib import Path
from datetime import datetime

from core.takeover_fingerprints import FINGERPRINTS

# DNS record types we want to look up for the main domain
RECORD_TYPES = ["A", "MX", "NS", "CNAME"]


# ===========================================================
# 1. DNS Resolution
# ===========================================================

def resolve_domain(domain):
    """
    Look up DNS records (A, MX, NS, CNAME) for a domain.

    Returns a dictionary like:
    {
        "domain": "example.com",
        "records": [
            {"type": "A", "value": "93.184.216.34"},
            {"type": "MX", "value": "mail.example.com"},
        ]
    }
    """
    results = {
        "domain": domain,
        "records": []
    }

    for record_type in RECORD_TYPES:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            for answer in answers:
                results["records"].append({
                    "type": record_type,
                    "value": answer.to_text()
                })
        except dns.resolver.NoAnswer:
            # This record type doesn't exist for this domain
            pass
        except dns.resolver.NXDOMAIN:
            results["error"] = "Domain does not exist"
            break
        except Exception as error:
            results["error"] = str(error)

    return results


# ===========================================================
# 2. SSL Certificate Info
# ===========================================================

def get_ssl_info(hostname):
    """
    Connect to a host on port 443 and read its SSL certificate.

    Returns a dictionary with issuer, expiry date, and subject.
    Returns None if SSL connection fails (e.g. no HTTPS).
    """
    try:
        # Create an SSL connection
        context = ssl.create_default_context()
        connection = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=hostname
        )
        connection.settimeout(5)
        connection.connect((hostname, 443))

        # Read the certificate
        cert = connection.getpeercert()
        connection.close()

        # Extract the useful parts
        issuer = dict(item[0] for item in cert.get("issuer", []))
        subject = dict(item[0] for item in cert.get("subject", []))

        return {
            "issuer": issuer.get("organizationName", "Unknown"),
            "subject": subject.get("commonName", "Unknown"),
            "expires": cert.get("notAfter", "Unknown"),
        }

    except Exception:
        return None


# ===========================================================
# 3. CNAME Lookup
# ===========================================================

def get_cnames(hostname):
    """
    Look up CNAME records for a hostname.

    CNAMEs are important for takeover detection because
    a dangling CNAME (pointing to an unclaimed resource)
    is what makes takeover possible.

    Returns a list of CNAME targets, or an empty list.
    """
    try:
        answers = dns.resolver.resolve(hostname, "CNAME")
        return [answer.to_text() for answer in answers]
    except Exception:
        return []


# ===========================================================
# 4. Subdomain Takeover Detection
# ===========================================================

def check_takeover(subdomain):
    """
    Check if a subdomain might be vulnerable to takeover.

    How it works:
    1. Fetch the HTTP page at the subdomain
    2. Compare the page content against known error messages
       from cloud providers (AWS, GitHub Pages, Heroku, etc.)
    3. If we find a match, the subdomain might be takeover-able

    Returns:
        {"risk": True, "provider": "GitHub Pages", "pattern": "..."}
        or
        {"risk": False}
    """
    try:
        response = requests.get(
            f"http://{subdomain}",
            timeout=5
        )
        body = response.text

        # Check the page against each provider's fingerprints
        for provider, patterns in FINGERPRINTS.items():
            for pattern in patterns:
                if pattern in body:
                    return {
                        "risk": True,
                        "provider": provider,
                        "pattern": pattern,
                    }

        return {"risk": False}

    except Exception:
        # Connection failed — not necessarily a takeover risk
        return {"risk": False}


# ===========================================================
# 5. Subdomain Enumeration (async)
# ===========================================================

async def resolve_subdomain(resolver, subdomain, domain):
    """
    Try to resolve one subdomain and gather all its info:
    - IP addresses
    - SSL certificate
    - CNAME records
    - Takeover risk

    Returns None if the subdomain doesn't exist.
    """
    target = f"{subdomain}.{domain}"

    try:
        # Try to resolve the subdomain's IP
        answer = await resolver.gethostbyname(target, socket.AF_INET)

        # If it resolved, gather extra info
        ssl_info = get_ssl_info(target)
        cnames = get_cnames(target)
        takeover = check_takeover(target)

        return {
            "subdomain": target,
            "ips": answer.addresses,
            "ssl": ssl_info,
            "cnames": cnames,
            "takeover": takeover,
        }

    except Exception:
        return None


async def enumerate_subdomains(domain):
    """
    Try every word in the wordlist as a subdomain.
    For example, if domain is "example.com" and wordlist has "www",
    we check if "www.example.com" exists.

    Returns a list of found subdomains with their details.
    """
    # Load the wordlist
    base_dir = Path(__file__).resolve().parent.parent.parent
    wordlist_path = base_dir / "resources" / "subdomains.txt"

    with open(wordlist_path) as file:
        subdomains = file.read().splitlines()

    # Create async DNS resolver and run all lookups at once
    resolver = aiodns.DNSResolver()

    tasks = []
    for subdomain in subdomains:
        tasks.append(resolve_subdomain(resolver, subdomain, domain))

    results = await asyncio.gather(*tasks)

    # Filter out None results (subdomains that don't exist)
    return [r for r in results if r is not None]
