# -------------------------------------------------------
# Domain Enumeration Module
# -------------------------------------------------------
# This module does 4 things:
#
#   1. Look up DNS records for the main domain
#   2. Find subdomains using a wordlist
#   3. Get SSL certificate info from crt.sh
#   4. Check for subdomain takeover risks
#
# For SSL certificates, we use crt.sh — a free website
# that shows all certificates issued for a domain.
# This is passive OSINT (we don't connect to the server).
#
# For takeover detection, we check if a subdomain has a
# CNAME pointing to a cloud service, then fetch the page
# to see if it shows an "unclaimed" error message.
# -------------------------------------------------------

import dns.resolver
import requests
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


# -------------------------------------------------------
# Takeover Detection Data
# -------------------------------------------------------
# Each cloud provider shows a specific error message when
# a resource (bucket, app, page) doesn't exist.
#
# "cnames" = domain patterns that point to this provider
# "content" = error messages that appear on unclaimed pages
# -------------------------------------------------------

TAKEOVER_SIGNATURES = {
    "AWS S3": {
        "cnames": [".s3.amazonaws.com", ".s3-website"],
        "content": ["NoSuchBucket"],
    },
    "GitHub Pages": {
        "cnames": [".github.io"],
        "content": ["There isn't a GitHub Pages site here"],
    },
    "Heroku": {
        "cnames": [".herokuapp.com", ".herokudns.com"],
        "content": ["No such app"],
    },
    "Azure": {
        "cnames": [".azurewebsites.net", ".cloudapp.net"],
        "content": ["ResourceNotFound"],
    },
    "Shopify": {
        "cnames": [".myshopify.com"],
        "content": ["Sorry, this shop is currently unavailable"],
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}


# -------------------------------------------------------
# 1. DNS Records
# -------------------------------------------------------

def get_dns_records(domain):
    """
    Look up DNS records (A, MX, NS, CNAME) for a domain.

    Returns a list like:
        [{"type": "A", "value": "93.184.216.34"}, ...]
    """
    records = []
    record_types = ["A", "MX", "NS", "CNAME"]

    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            for answer in answers:
                records.append({
                    "type": record_type,
                    "value": answer.to_text()
                })
        except Exception:
            # This record type doesn't exist for this domain — skip it
            pass

    return records


# -------------------------------------------------------
# 2. Subdomain Enumeration
# -------------------------------------------------------

def check_subdomain(subdomain):
    """
    Try to resolve a subdomain to an IP address.

    Returns a dictionary with the subdomain and its IP,
    or None if the subdomain doesn't exist.
    """
    try:
        ip = socket.gethostbyname(subdomain)
        return {"subdomain": subdomain, "ip": ip}
    except socket.gaierror:
        return None


def find_subdomains(domain):
    """
    Try every word in the wordlist as a subdomain prefix.
    For example: "www" + "example.com" = "www.example.com"

    Uses threads to check multiple subdomains at the same time.
    Returns a list of found subdomains with their IPs.
    """
    # Load the wordlist file
    base_dir = Path(__file__).resolve().parent.parent
    wordlist = base_dir / "resources" / "subdomains.txt"

    with open(wordlist) as file:
        prefixes = file.read().splitlines()

    # Build the full subdomain names
    targets = [f"{prefix}.{domain}" for prefix in prefixes]

    # Check all subdomains at the same time using threads
    found = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = pool.map(check_subdomain, targets)
        for result in results:
            if result is not None:
                found.append(result)

    return found


# -------------------------------------------------------
# 3. SSL Certificate Info (from crt.sh)
# -------------------------------------------------------

def get_ssl_certificates(domain):
    """
    Get SSL certificate info from crt.sh (Certificate Transparency logs).

    crt.sh is a free public website that lists all SSL certificates
    ever issued for a domain. This is passive OSINT — we don't need
    to connect to the actual server.

    Returns a dictionary mapping subdomains to their certificate info:
        {"www.example.com": {"expires": "2030-03-01", "issuer": "Let's Encrypt"}}
    """
    try:
        # Query crt.sh for all certificates matching this domain
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return {}

        certs = response.json()
    except Exception:
        return {}

    # Build a lookup table: subdomain -> latest certificate info
    # crt.sh returns many results, we only keep the most recent per subdomain
    cert_info = {}

    for cert in certs:
        # name_value can contain multiple domains separated by newlines
        names = cert.get("name_value", "").split("\n")
        expires = cert.get("not_after", "Unknown")
        issuer = cert.get("issuer_name", "Unknown")

        # Clean up the issuer name (it comes in a long format)
        # Example: "C=US, O=Let's Encrypt, CN=R3" -> "Let's Encrypt"
        issuer_short = issuer
        if "O=" in issuer:
            for part in issuer.split(","):
                if "O=" in part:
                    issuer_short = part.split("O=")[1].strip()
                    break

        for name in names:
            name = name.strip()
            # Skip wildcard entries like "*.example.com"
            if name.startswith("*"):
                continue
            # Only keep the most recent certificate per subdomain
            if name not in cert_info:
                cert_info[name] = {
                    "expires": expires,
                    "issuer": issuer_short,
                }

    return cert_info


def get_ssl_direct(hostname):
    """
    Fallback: get SSL certificate info by connecting to the server directly.
    Used when crt.sh is unavailable (it goes down often).

    Connects to port 443 and reads the certificate.
    Returns a dictionary with expiry and issuer, or None if no SSL.
    """
    try:
        context = ssl.create_default_context()
        with context.wrap_socket(socket.socket(), server_hostname=hostname) as conn:
            conn.settimeout(5)
            conn.connect((hostname, 443))
            cert = conn.getpeercert()

        # Extract expiry date
        expires = cert.get("notAfter", "Unknown")

        # Extract issuer organization
        issuer_parts = dict(item[0] for item in cert.get("issuer", []))
        issuer = issuer_parts.get("organizationName", "Unknown")

        return {"expires": expires, "issuer": issuer}

    except Exception:
        return None


# -------------------------------------------------------
# 4. Subdomain Takeover Detection
# -------------------------------------------------------

def get_cname(subdomain):
    """
    Get the CNAME record for a subdomain.

    A CNAME is like a redirect — it says "this subdomain
    actually points to this other domain".

    Example: blog.example.com -> example.github.io

    If the CNAME target no longer exists, the subdomain
    might be vulnerable to takeover.
    """
    try:
        answers = dns.resolver.resolve(subdomain, "CNAME")
        # Return the first CNAME target
        return answers[0].to_text()
    except Exception:
        return None


def check_takeover(subdomain, cname):
    """
    Check if a subdomain might be vulnerable to takeover.

    How it works:
    1. Look at the CNAME — does it point to a cloud provider?
    2. Fetch the page — does it show an "unclaimed" error?
    3. If both match, the subdomain might be takeover-able.

    Returns a dictionary like:
        {"vulnerable": True, "provider": "AWS S3", "reason": "..."}
    or:
        {"vulnerable": False}
    """
    if not cname:
        return {"vulnerable": False}

    # Step 1: Check if the CNAME points to a known cloud provider
    matched_provider = None
    for provider, data in TAKEOVER_SIGNATURES.items():
        for pattern in data["cnames"]:
            if pattern in cname:
                matched_provider = provider
                break
        if matched_provider:
            break

    if not matched_provider:
        return {"vulnerable": False}

    # Step 2: Fetch the page and check for error messages
    try:
        response = requests.get(
            f"http://{subdomain}",
            headers=HEADERS,
            timeout=5
        )
        page_content = response.text

        for fingerprint in TAKEOVER_SIGNATURES[matched_provider]["content"]:
            if fingerprint in page_content:
                return {
                    "vulnerable": True,
                    "provider": matched_provider,
                    "cname": cname,
                    "reason": f"CNAME points to {cname} but the resource appears unclaimed",
                }

    except Exception:
        # Connection failed — could also indicate the target doesn't exist
        return {
            "vulnerable": True,
            "provider": matched_provider,
            "cname": cname,
            "reason": f"CNAME points to {cname} but the target is not responding",
        }

    return {"vulnerable": False}


# -------------------------------------------------------
# 5. Full Domain Scan (combines everything above)
# -------------------------------------------------------

def scan(domain):
    """
    Run a complete scan on a domain:
    1. Get DNS records
    2. Find subdomains
    3. Get SSL certificate info
    4. Check each subdomain for takeover risk

    Returns a dictionary with all the results.
    """
    # Get DNS records for the main domain
    dns_records = get_dns_records(domain)

    # Find subdomains using the wordlist
    subdomains = find_subdomains(domain)

    # Get SSL certificate info from crt.sh (one request for all subdomains)
    all_certs = get_ssl_certificates(domain)

    # For each found subdomain, get CNAME and check for takeover
    takeover_risks = []

    for sub in subdomains:
        name = sub["subdomain"]

        # Get CNAME record
        cname = get_cname(name)
        sub["cname"] = cname

        # Match SSL certificate info from crt.sh
        if name in all_certs:
            sub["ssl"] = all_certs[name]
        else:
            sub["ssl"] = None

        # Check for takeover risk
        takeover = check_takeover(name, cname)
        sub["takeover"] = takeover

        if takeover["vulnerable"]:
            takeover_risks.append(sub)

    return {
        "domain": domain,
        "dns_records": dns_records,
        "subdomains": subdomains,
        "takeover_risks": takeover_risks,
    }
