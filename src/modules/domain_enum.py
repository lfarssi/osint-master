import dns.resolver
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


def enumerate_subdomains(domain):
    found=[]
    BASE_DIR=Path(__file__).resolve().parent.parent.parent
    WORDLIST=BASE_DIR / "resources" / "subdomains.txt"
    with open("resources/subdomains.txt" ) as file:
        subdomains=file.read().splitlines()
    for subdomain in subdomains:
        target= f"{subdomain}.{domain}"
        try:
            answers=dns.resolver.resolve(target, "A")
            ips=[answer.to_text() for answer in answers]
            found.append({
                "subdomain":subdomain,
                "ips":ips
            })
        except:
            continue
    return found
