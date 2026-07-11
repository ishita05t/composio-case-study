"""Dependency-free research-orchestration checkpoint for the case study.

This does not invent research. It validates structured claims and emits a
stratified audit queue for a browser/MCP worker plus a human reviewer.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REQUIRED = ("name", "category", "auth", "access", "surface", "verdict", "source")


def load_records(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"const appRows = (\[.*?\]);", text, re.S)
    if not match:
        raise ValueError("Could not find `const appRows = [...]` in input")
    rows = json.loads(match.group(1))
    # Mirror the deliberately conservative triage rules in apps.js. A browser/MCP
    # worker enriches this seed record with retrieved citations and excerpts.
    gated = {"DealCloud","Gladly","GoHighLevel","systeme.io","Salesforce Commerce Cloud","Amazon Selling Partner","Waterfall.io","PitchBook","NotebookLM","Consensus","Devin","higgsfield","YouTube Transcript"}
    admin = {"Salesforce","Zoho CRM","DealCloud","Front","Pylon","LiveAgent","Gladly","Zoho Cliq","Lark","WhatsApp Business","Aircall","Google Ads","Meta Ads","LinkedIn Ads","Threads","Salesforce Commerce Cloud","Magento / Adobe Commerce","Amazon Selling Partner","Bright Data","Waterfall.io","Clay","Snowflake","MongoDB Atlas","Smartsheet","QuickBooks","PitchBook","NotebookLM","Otter AI","Grain"}
    no_public = {"Twenty","Pylon","Plain","Pumble","systeme.io","fanbasis","Waterfall.io","NotebookLM","Consensus","higgsfield","Grain"}
    keys = {"Twilio","Telegram","SendGrid","DataForSEO","SE Ranking","Ahrefs","Apify","Firecrawl","Bright Data","Cloudflare","Supabase","Datadog","Stripe","Plaid","Binance","Paygent Connect","iPayX","Brex","Ramp","Reducto","Mermaid CLI","YouTube Transcript"}
    oauth = {"Slack","Discord","Lark","WhatsApp Business","Google Ads","Meta Ads","LinkedIn Ads","Pinterest","Threads","Shopify","BigCommerce","Squarespace","Ecwid","GitHub","Vercel","Netlify","Notion","Airtable","Linear","Jira","Asana","Monday.com","ClickUp","Coda","QuickBooks","Xero","Otter AI","Devin"}
    records = []
    for index, (category, name, hint) in enumerate(rows, 1):
        access = "Gated" if name in gated else "Admin" if name in admin else "Self-serve"
        surface = "No public API confirmed" if name in no_public else "Documented REST • focused"
        records.append({"id": index, "name": name, "category": category,
                        "auth": "OAuth 2.0" if name in oauth else "API key / token" if name in keys else "Token or API key",
                        "access": access, "surface": surface,
                        "verdict": "Outreach" if name in gated else "Validate" if name in admin or name in no_public else "Build now",
                        "source": f"https://{hint}"})
    return records


def readiness(record: dict) -> str:
    source = record["source"]
    if record["access"] == "Gated":
        return "Outreach"
    if "No public API" in record["surface"]:
        return "Not now"
    if record["access"] == "Admin" or "enterprise" in source.lower():
        return "Validate"
    return "Build now"


def stratified_sample(records: list[dict], limit: int) -> list[dict]:
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in records:
        buckets[(item["category"], readiness(item))].append(item)
    chosen = []
    for key in sorted(buckets):
        chosen.append(buckets[key][0])
        if len(chosen) == limit:
            return chosen
    for item in records:
        if item not in chosen:
            chosen.append(item)
            if len(chosen) == limit:
                break
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="apps.js")
    parser.add_argument("--output", default="research-run.json")
    parser.add_argument("--sample", type=int, default=12)
    parser.add_argument("--check-sources", action="store_true", help="HTTP-check first-party starting points")
    args = parser.parse_args()
    records = load_records(Path(args.input))
    failures = [{"app": r.get("name", "unknown"), "missing": [k for k in REQUIRED if not r.get(k)]}
                for r in records if any(not r.get(k) for k in REQUIRED)]
    for record in records:
        record["agent_verdict"] = readiness(record)
    report = {
        "run_at": datetime.now(UTC).isoformat(),
        "records": len(records),
        "required_field_failures": failures,
        "by_category": dict(Counter(r["category"] for r in records)),
        "by_auth": dict(Counter(r["auth"] for r in records)),
        "by_readiness": dict(Counter(r["agent_verdict"] for r in records)),
        "verification_queue": [{k: r[k] for k in ("name", "category", "auth", "access", "source")}
                               for r in stratified_sample(records, args.sample)],
    }
    if args.check_sources:
        checks = []
        for record in records:
            try:
                request = urllib.request.Request(record["source"], method="HEAD", headers={"User-Agent": "ToolScoutResearch/1.0"})
                with urllib.request.urlopen(request, timeout=12) as response:
                    checks.append({"app": record["name"], "status": response.status})
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                checks.append({"app": record["name"], "status": "unreachable", "detail": str(exc)[:120]})
        report["source_checks"] = checks
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Validated {len(records)} records; {len(failures)} required-field failures.")
    print(f"Wrote {args.output} with a {len(report['verification_queue'])}-app review queue.")


if __name__ == "__main__":
    main()
