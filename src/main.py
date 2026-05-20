import argparse
from core.validators import (validate_ip, validate_domain, validate_username)
from modules.ip_lookup import ip_lookup
from modules.username_lookup import username_lookup
from core.utils import save_output

def main():
    parser =argparse.ArgumentParser(
        description="OSINT Multi-Function Tool"
    )
    parser.add_argument("-i","--ip",help="Search information by IP address")
    parser.add_argument("-u","--username", help="Search information by username")
    parser.add_argument("-d","--domain",help="Enumerate domain information")
    parser.add_argument("-o","--output",help="Output file name")
    args=parser.parse_args()
    if args.ip:
        if not validate_ip(args.ip):
            print("Invalid IP address format")
            return
        result = ip_lookup(args.ip)
        if result["success"]:
            print(f"Country: {result['country']}")
            print(f"State: {result['state']}")
            print(f"City: {result['city']}")
            print(f"ISP: {result['isp']}")
            print(f"ASN: {result['asn']}")
            print(f"Location: {result['location']}")
            print(f"Timezone: {result['timezone']}")
            print(f"Query: {result['query']}")
            print(f"Proxy: {result['proxy']}")
            print(f"Hosting: {result['hosting']}")
            print(f"Organization: {result['org']}")
        else:
            print(f"Error: {result['error']}")
            return
    if args.domain:
        if not validate_domain(args.domain):
            print("Invalid Domain name")
            return
    if args.username:
        if not validate_username(args.username):
            print("Invalid Username")
            return
        result=username_lookup(args.username)
        for platform, status in result.items():
            print(f"{platform}: {status}")
            
    if args.output:
        save_output(args.output, result)
        print(f"Saved to output/{args.output}")
    print(args)


if __name__ == "__main__":
    main()