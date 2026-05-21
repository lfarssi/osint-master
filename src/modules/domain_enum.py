import socket
import dns.resolver
import asyncio
import aiodns
from pathlib import Path
RECORD_TYPES=[
    "A",
    "MX",
    "NS",
    "CNAME"
    ]


def resolve_domain(domain):
    results={
        "domain":domain,
        "records":[]
    }
    try:
        for record_type in RECORD_TYPES:
            answers=dns.resolver.resolve(domain,record_type)
            for answer in answers:
                results["records"].append({
                        "type":record_type,
                        "Value": answer.to_text()
            })
    except Exception as e:
        results["error"]=str(e)
    return results


async def resolve_subdomain(resolver, target):
    try:
        answer = await resolver.gethostbyname(
            target,
            socket.AF_INET
        )
        return {
            "subdomain":target,
            "ips": answer.addresses
        }
    except Exception:
        return None

async def enumerate_subdomains(domain):
    found=[]
    BASE_DIR=Path(__file__).resolve().parent.parent.parent
    WORDLIST=BASE_DIR / "resources" / "subdomains.txt"
    with open(WORDLIST) as file:
        subdomains=file.read().splitlines()
    resolver=aiodns.DNSResolver()
    for subdomain in subdomains:
        target= f"{subdomain}.{domain}"
        found.append(resolve_subdomain(resolver, target))
    results= await asyncio.gather(*found)
    return [result for result in results if result is not None]
