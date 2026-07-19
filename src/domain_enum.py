import dns.resolver
import requests
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


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
            pass

    return records



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
    base_dir = Path(__file__).resolve().parent.parent
    wordlist = base_dir / "resources" / "subdomains.txt"

    with open(wordlist) as file:
        prefixes = file.read().splitlines()

    targets = [f"{prefix}.{domain}" for prefix in prefixes]

    found = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = pool.map(check_subdomain, targets)
        for result in results:
            if result is not None:
                found.append(result)

    return found


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
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return {}

        certs = response.json()
    except Exception:
        return {}


    cert_info = {}

    for cert in certs:
        names = cert.get("name_value", "").split("\n")
        expires = cert.get("not_after", "Unknown")
        issuer = cert.get("issuer_name", "Unknown")

        issuer_short = issuer
        if "O=" in issuer:
            for part in issuer.split(","):
                if "O=" in part:
                    issuer_short = part.split("O=")[1].strip()
                    break

        for name in names:
            name = name.strip()
            if name.startswith("*"):
                continue
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

        expires = cert.get("notAfter", "Unknown")

        issuer_parts = dict(item[0] for item in cert.get("issuer", []))
        issuer = issuer_parts.get("organizationName", "Unknown")

        return {"expires": expires, "issuer": issuer}

    except Exception:
        return None


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
        return {
            "vulnerable": True,
            "provider": matched_provider,
            "cname": cname,
            "reason": f"CNAME points to {cname} but the target is not responding",
        }

    return {"vulnerable": False}


def scan(domain):
    """
    Run a complete scan on a domain:
    1. Get DNS records
    2. Find subdomains
    3. Get SSL certificate info
    4. Check each subdomain for takeover risk

    Returns a dictionary with all the results.
    """
    dns_records = get_dns_records(domain)

    subdomains = find_subdomains(domain)

    all_certs = get_ssl_certificates(domain)

    takeover_risks = []

    for sub in subdomains:
        name = sub["subdomain"]

        cname = get_cname(name)
        sub["cname"] = cname

        if name in all_certs:
            sub["ssl"] = all_certs[name]
        else:
            sub["ssl"] = None

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
