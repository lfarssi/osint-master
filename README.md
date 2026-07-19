# OSINT Master

A command-line OSINT (Open Source Intelligence) tool built with Python.

It can look up information about **IP addresses**, **usernames**, and **domains** — including subdomain enumeration and subdomain takeover detection.

## Features

- **IP Lookup** — Get geolocation, ISP, ASN, timezone, and more for any public IP
- **Username Search** — Check if a username exists on GitHub, Reddit, GitLab, Pinterest
- **Domain Enumeration** — Look up DNS records (A, MX, NS, CNAME) for any domain
- **Subdomain Discovery** — Find subdomains using a wordlist with async DNS resolution
- **SSL Certificate Info** — Show issuer, subject, and expiry for each subdomain
- **Subdomain Takeover Detection** — Check subdomains against known cloud provider fingerprints (AWS S3, GitHub Pages, Heroku, Azure, etc.)
- **JSON Export** — Save all results to a structured JSON file

## Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/osint-master.git
cd osint-master

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

Run from the `src/` directory:

```bash
cd src

# IP Lookup
python main.py -i 8.8.8.8

# Username Search
python main.py -u john_doe

# Domain Enumeration (includes subdomains, SSL, and takeover detection)
python main.py -d example.com

# Save results to JSON
python main.py -d example.com -o my_scan

# Combine multiple lookups
python main.py -i 8.8.8.8 -u john_doe -d example.com -o full_scan
```

## Project Structure

```
osint-master/
├── src/
│   ├── main.py                  # Entry point — CLI arguments and output formatting
│   ├── core/
│   │   ├── http_client.py       # HTTP GET wrapper (used by IP lookup)
│   │   ├── validators.py        # Input validation (IP, domain, username)
│   │   ├── utils.py             # Save results to JSON
│   │   └── takeover_fingerprints.py  # Cloud provider error fingerprints
│   └── modules/
│       ├── ip_lookup.py         # IP geolocation lookup (ip-api.com)
│       ├── username_lookup.py   # Async username search across platforms
│       └── domain_enum.py       # DNS resolution, subdomain enum, takeover check
├── resources/
│   └── subdomains.txt           # Wordlist for subdomain enumeration
├── output/                      # JSON output files (created automatically)
├── requirements.txt
└── README.md
```

## APIs Used

| API | Purpose | Auth Required |
|-----|---------|---------------|
| [ip-api.com](http://ip-api.com) | IP geolocation | No (free tier) |
| GitHub API | Username lookup | No |
| Reddit | Username lookup | No |
| GitLab | Username lookup | No |
| Pinterest | Username lookup | No |

## How Subdomain Takeover Detection Works

1. We enumerate subdomains by trying each word in the wordlist (e.g., `www`, `api`, `dev`)
2. For each found subdomain, we fetch its HTTP page
3. We check the page content against known error messages from cloud providers
4. If a match is found (e.g., "NoSuchBucket" from AWS), the subdomain might be vulnerable

**Why this matters:** If a subdomain's CNAME points to an unclaimed cloud resource (like a deleted S3 bucket), an attacker could register that resource and take control of the subdomain.

**Limitations:**
- This is a basic check (Version 1) — it only checks HTTP page content
- It doesn't verify CNAME targets directly
- False positives are possible
- Always verify findings manually

## Ethical Considerations

This tool is for **educational and authorized testing purposes only**.

- Only scan domains and IPs you own or have explicit permission to test
- Respect rate limits on APIs
- Do not use this tool for malicious purposes
- Follow your local laws regarding OSINT and network scanning

## Why Python?

- Rich ecosystem of libraries for DNS, HTTP, and async operations
- `dnspython` and `aiodns` make DNS resolution simple and fast
- `asyncio` + `aiohttp` allow checking many targets concurrently
- Easy to read and maintain for a team project

## Why Async?

Subdomain enumeration checks many hostnames. Doing this one-by-one would be slow. With async (`aiodns`, `aiohttp`), we send all DNS queries at once and process them as they come back. This makes enumeration much faster.