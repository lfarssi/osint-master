import dns.resolver

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