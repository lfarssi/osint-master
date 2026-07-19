# ----------------------------------------------------------
# OSINT Multi-Function Tool — Main Entry Point
# ----------------------------------------------------------
# Usage:
#   python main.py -i 8.8.8.8              (IP lookup)
#   python main.py -u john_doe             (username search)
#   python main.py -d example.com          (domain enum)
#   python main.py -d example.com -o results   (save to JSON)
#
# You can combine flags:
#   python main.py -i 8.8.8.8 -u john -o scan
# ----------------------------------------------------------

import argparse
import asyncio

from core.validators import validate_ip, validate_domain, validate_username
from core.utils import save_output
from modules.ip_lookup import ip_lookup
from modules.username_lookup import username_lookup
from modules.domain_enum import resolve_domain, enumerate_subdomains


# ===========================================================
# Output Formatting
# ===========================================================
# These functions turn raw dictionaries into clean,
# human-readable text so the terminal output looks nice.
# ===========================================================

def print_header(title):
    """Print a section header with a line underneath."""
    print()
    print(f"{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def print_ip_results(result):
    """Print IP lookup results in a clean format."""
    print_header("IP Lookup Results")

    if not result["success"]:
        print(f"  Error: {result['error']}")
        return

    print(f"  IP:           {result['ip']}")
    print(f"  Country:      {result['country']}")
    print(f"  State:        {result['state']}")
    print(f"  City:         {result['city']}")
    print(f"  ISP:          {result['isp']}")
    print(f"  Organization: {result['org']}")
    print(f"  ASN:          {result['asn']}")
    print(f"  Location:     {result['location']}")
    print(f"  Timezone:     {result['timezone']}")
    print(f"  Proxy:        {result['proxy']}")
    print(f"  Hosting:      {result['hosting']}")


def print_domain_results(dns_results, subdomains):
    """Print domain enumeration results in a clean format."""
    print_header(f"Domain: {dns_results['domain']}")

    # Show DNS records
    if dns_results.get("error"):
        print(f"  DNS Error: {dns_results['error']}")
    else:
        print("\n  DNS Records:")
        for record in dns_results["records"]:
            print(f"    {record['type']:6s}  {record['value']}")

    # Show subdomains
    if not subdomains:
        print("\n  No subdomains found.")
        return

    print(f"\n  Found {len(subdomains)} subdomain(s):")

    for sub in subdomains:
        print(f"\n  {'─' * 44}")
        print(f"  Subdomain: {sub['subdomain']}")

        # IPs
        print(f"  IPs:")
        for ip in sub["ips"]:
            print(f"    - {ip}")

        # CNAME records
        if sub["cnames"]:
            print(f"  CNAMEs:")
            for cname in sub["cnames"]:
                print(f"    - {cname}")

        # SSL info
        if sub["ssl"]:
            print(f"  SSL:")
            print(f"    Issuer:  {sub['ssl']['issuer']}")
            print(f"    Subject: {sub['ssl']['subject']}")
            print(f"    Expires: {sub['ssl']['expires']}")
        else:
            print(f"  SSL: No HTTPS")

        # Takeover risk
        if sub["takeover"]["risk"]:
            print(f"  Takeover Risk: YES")
            print(f"    Provider: {sub['takeover']['provider']}")
            print(f"    Pattern:  {sub['takeover']['pattern']}")
        else:
            print(f"  Takeover Risk: No")


def print_username_results(results):
    """Print username lookup results in a clean format."""
    print_header("Username Lookup Results")

    for platform, status in results.items():
        # Add a checkmark or X for quick scanning
        icon = "+" if status == "Found" else "-"
        print(f"  [{icon}] {platform:12s}  {status}")


# ===========================================================
# Main Function
# ===========================================================

def main():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(
        description="OSINT Multi-Function Tool"
    )
    parser.add_argument("-i", "--ip", help="Look up info for an IP address")
    parser.add_argument("-u", "--username", help="Search for a username on platforms")
    parser.add_argument("-d", "--domain", help="Enumerate a domain (DNS + subdomains)")
    parser.add_argument("-o", "--output", help="Save results to a JSON file")

    args = parser.parse_args()

    # We'll collect all results here for saving to JSON later
    all_results = {}

    # --- IP Lookup ---
    if args.ip:
        if not validate_ip(args.ip):
            print("Error: Invalid IP address format.")
            return
        result = ip_lookup(args.ip)
        print_ip_results(result)
        all_results["ip_lookup"] = result

    # --- Domain Enumeration ---
    if args.domain:
        if not validate_domain(args.domain):
            print("Error: Invalid domain name.")
            return
        dns_results = resolve_domain(args.domain)
        subdomains = asyncio.run(enumerate_subdomains(args.domain))
        print_domain_results(dns_results, subdomains)
        all_results["domain"] = {
            "dns": dns_results,
            "subdomains": subdomains
        }

    # --- Username Lookup ---
    if args.username:
        if not validate_username(args.username):
            print("Error: Invalid username (use 3-30 chars: letters, numbers, . _ -).")
            return
        result = asyncio.run(username_lookup(args.username))
        print_username_results(result)
        all_results["username_lookup"] = result

    # --- Save to JSON ---
    if args.output and all_results:
        print_header("Saving Results")
        save_output(args.output, all_results)

    # If no arguments were given, show help
    if not any([args.ip, args.domain, args.username]):
        parser.print_help()


if __name__ == "__main__":
    main()