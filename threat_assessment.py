#!/usr/bin/env python3

import json
import sys
import re
import requests
from datetime import datetime
from urllib.parse import urlparse


# ==================================================
# CONFIG
# ==================================================

VT_API_KEY = "835df2753f2fb40dd399952f3a7bcab62ff434a98a0c194cdf85d474b5e2a5d3"   

TIMEOUT = 5


# ==================================================
# TOP 50 TRUSTED SOURCES
# ==================================================

TRUSTED_SOURCES = [

    # Government / Standards
    "nist",
    "nvd",
    "cisa",
    "mitre",
    "us-cert",
    "cert-in",
    "enisa",
    "govcert",
    "ncsc",
    "anssi",

    # Big Tech
    "microsoft",
    "google",
    "amazon",
    "aws",
    "meta",
    "facebook",
    "apple",
    "ibm",
    "oracle",
    "intel",

    # Security Companies
    "kaspersky",
    "crowdstrike",
    "fireeye",
    "mandiant",
    "palo alto",
    "checkpoint",
    "trend micro",
    "symantec",
    "mcafee",
    "bitdefender",

    # Research / Intel
    "talos",
    "recorded future",
    "rapid7",
    "proofpoint",
    "unit42",
    "secureworks",
    "elastic",
    "sophos",
    "fortinet",
    "sentinelone",

    # Community / Open
    "virus total",
    "abuse.ch",
    "malwarebytes",
    "openphish",
    "phishtank"
]


# ==================================================
# HELPERS
# ==================================================

def load_bundle(path):

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("❌ Cannot load file:", e)
        sys.exit(1)


def normalize(text):

    return text.lower().strip()


def contains_trusted(name):

    name = normalize(name)

    for src in TRUSTED_SOURCES:
        if src in name:
            return True

    return False


def parse_date(val):

    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except:
        return None


# ==================================================
# VIRUSTOTAL CHECK
# ==================================================

def check_virustotal(ioc):

    if not VT_API_KEY:
        return None

    headers = {
        "x-apikey": VT_API_KEY
    }

    url = f"https://www.virustotal.com/api/v3/search?query={ioc}"

    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)

        if r.status_code == 200:

            data = r.json()

            if data.get("data"):
                return True

    except:
        pass

    return False


# ==================================================
# URL CHECK
# ==================================================

def check_url(url):

    try:
        r = requests.head(url, timeout=TIMEOUT, allow_redirects=True)

        if r.status_code < 400:
            return True

    except:
        pass

    return False


# ==================================================
# MAIN ANALYZER
# ==================================================

def analyze_bundle(bundle):

    score = 0
    reasons = []


    # ----------------------------------------------
    # 1. Basic Format
    # ----------------------------------------------

    if bundle.get("type") == "bundle":
        score += 10
        reasons.append("✔ Valid STIX bundle format")
    else:
        reasons.append("❌ Invalid STIX format")


    objects = bundle.get("objects", [])

    if objects:
        score += 5
        reasons.append("✔ Objects present")
    else:
        reasons.append("❌ No objects")


    # ----------------------------------------------
    # 2. Identify Objects
    # ----------------------------------------------

    identities = []
    relationships = []
    reports = []
    indicators = []
    malware = []
    external_urls = []

    for obj in objects:

        t = obj.get("type")

        if t == "identity":
            identities.append(obj)

        elif t == "relationship":
            relationships.append(obj)

        elif t == "report":
            reports.append(obj)

        elif t == "indicator":
            indicators.append(obj)

        elif t == "malware":
            malware.append(obj)

        # Extract URLs
        for ref in obj.get("external_references", []):
            url = ref.get("url")
            if url:
                external_urls.append(url)


    # ----------------------------------------------
    # 3. Trusted Sources
    # ----------------------------------------------

    trusted_found = False

    for ident in identities:

        name = ident.get("name", "")

        if contains_trusted(name):
            trusted_found = True
            break


    if trusted_found:
        score += 20
        reasons.append("✔ Trusted organization identified")
    else:
        reasons.append("⚠ No major trusted source found")


    # ----------------------------------------------
    # 4. Relationships / Linking
    # ----------------------------------------------

    linked = False

    if relationships:
        linked = True

    # Report refs also count
    for r in reports:
        if r.get("object_refs"):
            linked = True


    if linked:
        score += 15
        reasons.append("✔ Objects properly linked")
    else:
        reasons.append("⚠ No strong object relationships")


    # ----------------------------------------------
    # 5. Timeline Check
    # ----------------------------------------------

    has_time = False

    for obj in objects:

        for field in [
            "created",
            "modified",
            "published",
            "first_seen",
            "last_seen"
        ]:

            if field in obj:
                dt = parse_date(obj[field])

                if dt:
                    has_time = True


    if has_time:
        score += 10
        reasons.append("✔ Timeline metadata present")
    else:
        reasons.append("⚠ Missing timeline data")


    # ----------------------------------------------
    # 6. Metadata Quality
    # ----------------------------------------------

    rich = 0

    for obj in objects:

        if obj.get("description"):
            rich += 1

        if obj.get("kill_chain_phases"):
            rich += 1

        if obj.get("external_references"):
            rich += 1


    if rich >= len(objects):
        score += 10
        reasons.append("✔ Rich technical metadata")

    else:
        reasons.append("⚠ Limited technical details")


    # ----------------------------------------------
    # 7. VirusTotal Check
    # ----------------------------------------------

    vt_hits = 0

    for ind in indicators:

        patt = ind.get("pattern", "")

        iocs = re.findall(r"'([^']+)'", patt)

        for ioc in iocs:

            if check_virustotal(ioc):
                vt_hits += 1


    if vt_hits:
        score += 15
        reasons.append(f"✔ {vt_hits} IOC confirmed by VirusTotal")

    elif indicators or malware:
        reasons.append("⚠ No IOC confirmed")


    # ----------------------------------------------
    # 8. URL Validation
    # ----------------------------------------------

    valid_urls = 0

    for url in external_urls:

        if check_url(url):
            valid_urls += 1


    if valid_urls:
        score += 10
        reasons.append("✔ Referenced URLs reachable")

    elif external_urls:
        reasons.append("⚠ Referenced URLs unreachable")


    # ----------------------------------------------
    # 9. Coverage
    # ----------------------------------------------

    if reports and (malware or indicators or relationships):
        score += 10
        reasons.append("✔ Good analytical coverage")


    # ----------------------------------------------
    # Clamp Score
    # ----------------------------------------------

    score = max(0, min(100, score))


    # ----------------------------------------------
    # Rating
    # ----------------------------------------------

    if score >= 75:
        rating = "HIGH"

    elif score >= 45:
        rating = "MEDIUM"

    else:
        rating = "LOW"


    # ----------------------------------------------
    # Summary
    # ----------------------------------------------

    summary = generate_summary(score, rating, reasons)


    return {
        "score": score,
        "rating": rating,
        "reasons": reasons,
        "summary": summary
    }


# ==================================================
# SUMMARY GENERATOR
# ==================================================

def generate_summary(score, rating, reasons):

    positives = [r for r in reasons if r.startswith("✔")]
    warnings = [r for r in reasons if r.startswith("⚠")]
    negatives = [r for r in reasons if r.startswith("❌")]

    lines = []

    lines.append(f"Overall credibility is {rating} ({score}/100).")

    if positives:
        lines.append("Strong factors:")
        for p in positives[:3]:
            lines.append(" - " + p[2:])

    if warnings:
        lines.append("Limitations:")
        for w in warnings[:3]:
            lines.append(" - " + w[2:])

    if negatives:
        lines.append("Critical issues:")
        for n in negatives[:2]:
            lines.append(" - " + n[2:])

    return "\n".join(lines)


# ==================================================
# MAIN
# ==================================================

def main():

    if len(sys.argv) != 2:
        print("Usage:")
        print("  python threat_credibility.py bundle.json")
        sys.exit(1)


    path = sys.argv[1]

    bundle = load_bundle(path)

    result = analyze_bundle(bundle)


    print("\n===== THREAT CREDIBILITY REPORT 2=====\n")

    print(f"Score       : {result['score']} / 100")
    print(f"Credibility : {result['rating']}\n")

    print("Explanation:")

    for r in result["reasons"]:
        print(" -", r)

    print("\nSummary:\n")
    print(result["summary"])

    print("\n====================================\n")


if __name__ == "__main__":
    main()
