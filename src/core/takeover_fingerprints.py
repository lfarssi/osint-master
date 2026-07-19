# ----------------------------------------------------------
# Subdomain Takeover Fingerprints
# ----------------------------------------------------------
# Each provider has a list of error messages that show up
# when the resource (bucket, app, page) does not exist.
#
# If we find one of these messages in a subdomain's HTTP
# response, it means that subdomain MIGHT be vulnerable
# to takeover — someone could register that resource and
# control the subdomain.
# ----------------------------------------------------------

FINGERPRINTS = {
    "AWS S3": [
        "NoSuchBucket",
    ],
    "GitHub Pages": [
        "There isn't a GitHub Pages site here",
    ],
    "Heroku": [
        "No such app",
    ],
    "Azure": [
        "ResourceNotFound",
    ],
    "Shopify": [
        "Sorry, this shop is currently unavailable",
    ],
    "Fastly": [
        "Fastly error: unknown domain",
    ],
    "Pantheon": [
        "404 error unknown site",
    ],
    "Tumblr": [
        "There's nothing here",
    ],
}
