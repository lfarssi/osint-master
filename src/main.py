import argparse
import json
import os
import re
import ipaddress
from pathlib import Path

from ip_lookup import lookup as ip_lookup
from username_lookup import lookup as username_lookup
from domain_enum import scan as domain_scan

def is_valid_ip(ip):
    """Check if the string is a valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_domain(domain):
    """Check if the string looks like a valid domain name."""
    pattern = r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
    return re.match(pattern, domain) is not None


def is_valid_username(username):
    """Check if the username contains only safe characters (3-30 chars)."""
    pattern = r"^[a-zA-Z0-9._@-]{1,50}$"
    return re.match(pattern, username) is not None



def format_ip_output(result):
    """Format IP lookup results as a readable string."""
    if not result["success"]:
        return f"Error: {result['error']}"

    lines = []
    lines.append(f"ISP: {result['isp']}")
    lines.append(f"Organization: {result['org']}")
    lines.append(f"City: {result['city']}")
    lines.append(f"Region: {result['region']}")
    lines.append(f"Country: {result['country']}")
    lines.append(f"ASN: {result['asn']}")
    lines.append(f"Known Issues: {', '.join(result['known_issues'])}")

    return "\n".join(lines)


def format_username_output(result):
    """Format username lookup results as a readable string."""
    lines = []

    for platform, status in result["platforms"].items():
        lines.append(f"{platform}: {status}")

    profile = result.get("github_profile")
    if profile:
        lines.append("")
        lines.append("GitHub Profile:")
        lines.append(f"  Bio: {profile['bio']}")
        lines.append(f"  Followers: {profile['followers']}")
        lines.append(f"  Following: {profile['following']}")
        lines.append(f"  Public Repos: {profile['public_repos']}")
        lines.append(f"  Last Active: {profile['last_active']}")

    return "\n".join(lines)


def format_domain_output(result):
    """Format domain scan results as a readable string."""
    lines = []

    lines.append(f"Main Domain: {result['domain']}")
    lines.append("")

    # DNS Records
    if result["dns_records"]:
        lines.append("DNS Records:")
        for record in result["dns_records"]:
            lines.append(f"  {record['type']:6s} {record['value']}")
        lines.append("")

    # Subdomains
    subdomains = result["subdomains"]
    lines.append(f"Subdomains found: {len(subdomains)}")

    for sub in subdomains:
        lines.append(f"  - {sub['subdomain']} (IP: {sub['ip']})")

        # SSL certificate info
        if sub.get("ssl"):
            lines.append(f"    SSL Certificate: Valid until {sub['ssl']['expires']}")
        else:
            lines.append(f"    SSL Certificate: Not found")

        # CNAME record
        if sub.get("cname"):
            lines.append(f"    CNAME: {sub['cname']}")

    # Takeover risks
    lines.append("")
    takeover_risks = result["takeover_risks"]

    if takeover_risks:
        lines.append("Potential Subdomain Takeover Risks:")
        for risk in takeover_risks:
            takeover = risk["takeover"]
            lines.append(f"  - Subdomain: {risk['subdomain']}")
            lines.append(f"    {takeover['reason']}")
            lines.append(f"    Provider: {takeover['provider']}")
            lines.append(f"    Recommended Action: Remove or update the DNS record to prevent potential misuse")
    else:
        lines.append("Potential Subdomain Takeover Risks: None detected")

    return "\n".join(lines)



def save_to_file(filename, text_output, raw_data):
    """
    Save results to the output/ directory.
    Creates two files:
      - filename.txt  (human-readable text)
      - filename.json (structured data for further processing)
    """
    output_dir = Path(__file__).resolve().parent.parent / "output"
    os.makedirs(output_dir, exist_ok=True)

    txt_path = output_dir / filename
    if not filename.endswith(".txt"):
        txt_path = output_dir / f"{filename}.txt"

    with open(txt_path, "w") as file:
        file.write(text_output)

    json_path = txt_path.with_suffix(".json")
    with open(json_path, "w") as file:
        json.dump(raw_data, file, indent=2)

    return txt_path



def main():
    parser = argparse.ArgumentParser(
        prog="osintmaster",
        description="Welcome to osintmaster multi-function Tool",
    )
    parser.add_argument("-i", metavar='"IP Address"', help="Search information by IP address")
    parser.add_argument("-u", metavar='"Username"', help="Search information by username")
    parser.add_argument("-d", metavar='"Domain"', help="Enumerate subdomains and check for takeover risks")
    parser.add_argument("-o", metavar='"FileName"', help="File name to save output")

    args = parser.parse_args()

    # If no arguments given, show help
    if not any([args.i, args.u, args.d]):
        parser.print_help()
        return

    all_output = []  
    all_data = {}    

    # --- IP Lookup ---
    if args.i:
        ip = args.i.strip('"')
        if not is_valid_ip(ip):
            print("Error: Invalid IP address.")
            return

        print(f"Looking up IP: {ip}...")
        result = ip_lookup(ip)
        output = format_ip_output(result)
        print(output)
        all_output.append(output)
        all_data["ip_lookup"] = result

    # --- Username Lookup ---
    if args.u:
        username = args.u.strip('"@')
        if not is_valid_username(username):
            print("Error: Invalid username.")
            return

        print(f"Searching for username: {username}...")
        result = username_lookup(username)
        output = format_username_output(result)
        print(output)
        all_output.append(output)
        all_data["username_lookup"] = result

    # --- Domain Scan ---
    if args.d:
        domain = args.d.strip('"')
        if not is_valid_domain(domain):
            print("Error: Invalid domain name.")
            return

        print(f"Scanning domain: {domain}...")
        print()
        result = domain_scan(domain)
        output = format_domain_output(result)
        print(output)
        all_output.append(output)
        all_data["domain_scan"] = result

    # --- Save to File ---
    if args.o:
        filename = args.o.strip('"')
        full_text = "\n\n".join(all_output)
        saved_path = save_to_file(filename, full_text, all_data)
        print(f"\nData saved in {saved_path}")


if __name__ == "__main__":
    main()