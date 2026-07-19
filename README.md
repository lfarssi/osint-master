# OSINT Master

A command-line OSINT (Open Source Intelligence) tool for passive reconnaissance using publicly available data.

## What It Does

| Feature | Description |
|---------|-------------|
| **IP Lookup** | Get geolocation, ISP, ASN, and abuse indicators for any public IP |
| **Username Search** | Check if a username exists on 5+ platforms + get GitHub profile details |
| **Domain Scan** | DNS records, subdomain discovery, SSL certificates, and takeover detection |

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Linux recommended (tested on Ubuntu 20.04+)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd osint-master

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Only **2 dependencies**: `requests` and `dnspython`. That's it.

## Usage

Run from the `src/` directory:

```bash
cd src
```

### IP Lookup

```bash
python main.py -i 8.8.8.8
```

Output:
```
ISP: Google LLC
Organization: Google Public DNS
City: Ashburn
Region: Virginia
Country: United States
ASN: AS15169 Google LLC
Known Issues: No reported abuse
```

### Username Search

```bash
python main.py -u johndoe
```

Output:
```
GitHub: Found
GitLab: Not Found
Reddit: Found
Pinterest: Not Found
Medium: Not Found

GitHub Profile:
  Bio: Software developer
  Followers: 42
  Public Repos: 15
  Last Active: 2026-07-19T10:00:00Z
```

### Domain Scan

```bash
python main.py -d example.com
```

Output:
```
Main Domain: example.com

DNS Records:
  A      93.184.216.34
  NS     a.iana-servers.net.

Subdomains found: 2
  - www.example.com (IP: 93.184.216.34)
    SSL Certificate: Valid until 2030-03-01
  - mail.example.com (IP: 93.184.216.34)
    SSL Certificate: Not found

Potential Subdomain Takeover Risks: None detected
```

### Save Results to File

```bash
python main.py -i 8.8.8.8 -o result1.txt
python main.py -u johndoe -o result2.txt
python main.py -d example.com -o result3.txt
```

Results are saved in the `output/` directory as both `.txt` (readable) and `.json` (structured).

### Help

```bash
python main.py --help
```

## Project Structure

```
osint-master/
├── src/
│   ├── main.py              # Entry point — CLI, validation, output formatting
│   ├── ip_lookup.py          # IP geolocation and abuse check (ip-api.com)
│   ├── username_lookup.py    # Username search across platforms
│   └── domain_enum.py        # DNS, subdomains, SSL, takeover detection
├── tests/                    # Test files
├── output/                   # Saved results (created automatically)
├── resources/
│   └── subdomains.txt        # Wordlist for subdomain enumeration
├── requirements.txt          # Python dependencies
├── .gitignore
└── README.md
```

## APIs and Data Sources

| Source | Used For | Auth Required | Cost |
|--------|----------|---------------|------|
| [ip-api.com](http://ip-api.com) | IP geolocation, ISP, abuse indicators | No | Free (non-commercial) |
| [GitHub API](https://api.github.com) | Username check + profile details | No | Free (rate limited) |
| [crt.sh](https://crt.sh) | SSL certificate transparency logs | No | Free |
| GitLab, Reddit, Pinterest, Medium | Username existence check | No | Free |

All APIs are used within their Terms of Service. No API keys required.

## How Subdomain Takeover Detection Works

**What is a subdomain takeover?**

When a subdomain (like `blog.example.com`) has a CNAME record pointing to a cloud service (like GitHub Pages or AWS S3), but the resource on that service has been deleted, an attacker could register that resource and take control of the subdomain.

**How we detect it:**

1. Find subdomains using a wordlist (e.g., `www`, `mail`, `api`, `blog`)
2. Check each subdomain's CNAME record — does it point to a cloud provider?
3. Fetch the page — does it show an "unclaimed resource" error message?
4. If both match, the subdomain is likely vulnerable

**Why CNAMEs matter:**

A CNAME is like a redirect. If `blog.example.com` has a CNAME pointing to `example.github.io`, and that GitHub Pages site no longer exists, anyone could create it and control what appears on `blog.example.com`.

**Supported providers:** AWS S3, GitHub Pages, Heroku, Azure, Shopify

**Limitations:**
- This checks HTTP content only (basic detection)
- False positives are possible
- Always verify findings manually before reporting

## How SSL Certificate Lookup Works

We use [crt.sh](https://crt.sh), a free Certificate Transparency (CT) log search engine. CT logs are public records of all SSL certificates issued by Certificate Authorities. This is passive OSINT — we query a public database instead of connecting to the target server.

## Ethical and Legal Considerations

⚠️ **This tool is for educational purposes only.**

- **Get permission** before gathering information about any target
- **Respect privacy** — collect only what's necessary
- **Follow laws** — comply with GDPR, CFAA, and local regulations
- **Report responsibly** — privately notify affected parties of vulnerabilities
- **Stay ethical** — use this tool only for learning and authorized security testing

The developers are not responsible for any misuse of this tool.

## Why Python?

- Simple and readable — easy for anyone to understand the code
- `requests` library makes HTTP calls straightforward
- `dnspython` handles all DNS operations cleanly
- `concurrent.futures` provides simple parallelism (no complex async)
- Large ecosystem of cybersecurity tools and libraries

## Known Limitations

- Username detection relies on HTTP status codes, which can give false results
- Subdomain wordlist is small (for demonstration) — expand it for real use
- SSL info comes from CT logs, which may not include very new certificates
- Takeover detection is basic (content fingerprinting only)
- ip-api.com has a rate limit of 45 requests per minute

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Make sure you activated the venv: `source venv/bin/activate` |
| `Connection timeout` | Check your internet connection |
| IP lookup returns error | The IP might be private (10.x, 192.168.x, etc.) |
| No subdomains found | The domain might not have common subdomain names |
| crt.sh timeout | crt.sh can be slow — the tool will continue without SSL info |