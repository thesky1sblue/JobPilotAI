"""
Discover and ingest India-specific tech companies & startups from Greenhouse and Lever.
Only retains opportunities based in India (Bangalore, Chennai, Hyderabad, Pune, Mumbai,
Delhi/NCR, Gurgaon, Noida, Kolkata, Remote India).
"""
import asyncio
import httpx
import sqlite3
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any

# Top Indian Tech Startups & Global Tech Hubs in India with Greenhouse or Lever public job boards
INDIAN_COMPANIES = [
    # Lever Boards
    {"name": "CRED", "domain": "cred.club", "careers_url": "https://careers.cred.club", "platform": "lever", "slug": "cred", "location": "Bangalore, India", "industry": "Fintech & Rewards", "is_indian_native": True},
    {"name": "Swiggy", "domain": "swiggy.com", "careers_url": "https://careers.swiggy.com", "platform": "lever", "slug": "swiggy", "location": "Bangalore, India", "industry": "FoodTech & QuickCommerce", "is_indian_native": True},
    {"name": "Razorpay", "domain": "razorpay.com", "careers_url": "https://razorpay.com/jobs", "platform": "lever", "slug": "razorpay", "location": "Bangalore, India", "industry": "Fintech & Payments", "is_indian_native": True},
    {"name": "Groww", "domain": "groww.in", "careers_url": "https://careers.groww.in", "platform": "lever", "slug": "groww", "location": "Bangalore, India", "industry": "WealthTech & Brokerage", "is_indian_native": True},
    {"name": "Urban Company", "domain": "urbancompany.com", "careers_url": "https://www.urbancompany.com/careers", "platform": "lever", "slug": "urbancompany", "location": "Gurgaon, India", "industry": "Home Services Marketplace", "is_indian_native": True},
    {"name": "ClearTax", "domain": "cleartax.in", "careers_url": "https://cleartax.in/careers", "platform": "lever", "slug": "cleartax", "location": "Bangalore, India", "industry": "Fintech & SaaS", "is_indian_native": True},
    {"name": "Hasura", "domain": "hasura.io", "careers_url": "https://hasura.io/careers", "platform": "lever", "slug": "hasura", "location": "Bangalore, India", "industry": "Developer Tools & GraphQL", "is_indian_native": True},
    {"name": "Setu", "domain": "setu.co", "careers_url": "https://setu.co/careers", "platform": "lever", "slug": "setu", "location": "Bangalore, India", "industry": "Open Banking & API Infrastructure", "is_indian_native": True},
    {"name": "smallcase", "domain": "smallcase.com", "careers_url": "https://careers.smallcase.com", "platform": "lever", "slug": "smallcase", "location": "Bangalore, India", "industry": "Investment Tech", "is_indian_native": True},
    {"name": "Jupiter Money", "domain": "jupiter.money", "careers_url": "https://jupiter.money/careers", "platform": "lever", "slug": "jupiter-money", "location": "Mumbai, India", "industry": "Neobanking & Fintech", "is_indian_native": True},
    {"name": "Slice", "domain": "sliceit.com", "careers_url": "https://sliceit.com/careers", "platform": "lever", "slug": "slice", "location": "Bangalore, India", "industry": "Consumer Fintech", "is_indian_native": True},
    {"name": "INDmoney", "domain": "indmoney.com", "careers_url": "https://indmoney.com/careers", "platform": "lever", "slug": "indmoney", "location": "Gurgaon, India", "industry": "WealthTech", "is_indian_native": True},
    {"name": "Games24x7", "domain": "games24x7.com", "careers_url": "https://www.games24x7.com/careers", "platform": "lever", "slug": "games24x7", "location": "Mumbai, India", "industry": "Gaming & AI", "is_indian_native": True},

    # Greenhouse Boards
    {"name": "Meesho", "domain": "meesho.com", "careers_url": "https://meesho.io/careers", "platform": "greenhouse", "slug": "meesho", "location": "Bangalore, India", "industry": "E-Commerce", "is_indian_native": True},
    {"name": "Postman", "domain": "postman.com", "careers_url": "https://www.postman.com/company/careers", "platform": "greenhouse", "slug": "postman", "location": "Bangalore, India", "industry": "API DevTools", "is_indian_native": True},
    {"name": "BrowserStack", "domain": "browserstack.com", "careers_url": "https://www.browserstack.com/careers", "platform": "greenhouse", "slug": "browserstack", "location": "Mumbai, India", "industry": "Cloud Testing", "is_indian_native": True},
    {"name": "Freshworks", "domain": "freshworks.com", "careers_url": "https://www.freshworks.com/company/careers", "platform": "greenhouse", "slug": "freshworks", "location": "Chennai, India", "industry": "SaaS", "is_indian_native": True},
    {"name": "Darwinbox", "domain": "darwinbox.com", "careers_url": "https://darwinbox.com/careers", "platform": "greenhouse", "slug": "darwinbox", "location": "Hyderabad, India", "industry": "HR Tech", "is_indian_native": True},
    {"name": "LeadSquared", "domain": "leadsquared.com", "careers_url": "https://www.leadsquared.com/careers", "platform": "greenhouse", "slug": "leadsquared", "location": "Bangalore, India", "industry": "CRM SaaS", "is_indian_native": True},
    {"name": "CleverTap", "domain": "clevertap.com", "careers_url": "https://clevertap.com/careers", "platform": "greenhouse", "slug": "clevertap", "location": "Mumbai, India", "industry": "Retention SaaS", "is_indian_native": True},
    {"name": "Capillary Technologies", "domain": "capillarytech.com", "careers_url": "https://www.capillarytech.com/careers", "platform": "greenhouse", "slug": "capillary", "location": "Bangalore, India", "industry": "Retail AI", "is_indian_native": True},
    {"name": "InMobi", "domain": "inmobi.com", "careers_url": "https://www.inmobi.com/company/careers", "platform": "greenhouse", "slug": "inmobi", "location": "Bangalore, India", "industry": "AdTech & AI", "is_indian_native": True},
    {"name": "Zeta", "domain": "zeta.tech", "careers_url": "https://www.zeta.tech/careers", "platform": "greenhouse", "slug": "zeta", "location": "Bangalore, India", "industry": "Cloud Banking", "is_indian_native": True},
    {"name": "Thoughtworks India", "domain": "thoughtworks.com", "careers_url": "https://www.thoughtworks.com/careers", "platform": "greenhouse", "slug": "thoughtworks", "location": "Bangalore, India", "industry": "Software Consultancy", "is_indian_native": False},
    {"name": "Sprinklr", "domain": "sprinklr.com", "careers_url": "https://www.sprinklr.com/careers", "platform": "greenhouse", "slug": "sprinklr", "location": "Gurgaon, India", "industry": "AI SaaS", "is_indian_native": False},
    {"name": "Harness", "domain": "harness.io", "careers_url": "https://harness.io/careers", "platform": "greenhouse", "slug": "harness", "location": "Bangalore, India", "industry": "DevOps AI", "is_indian_native": False},
    {"name": "Elastic India", "domain": "elastic.co", "careers_url": "https://www.elastic.co/about/careers", "platform": "greenhouse", "slug": "elastic", "location": "Bangalore, India", "industry": "Search & Observability", "is_indian_native": False},
    {"name": "Confluent India", "domain": "confluent.io", "careers_url": "https://www.confluent.io/careers", "platform": "greenhouse", "slug": "confluent", "location": "Bangalore, India", "industry": "Data Streaming", "is_indian_native": False},
    {"name": "MongoDB India", "domain": "mongodb.com", "careers_url": "https://www.mongodb.com/careers", "platform": "greenhouse", "slug": "mongodb", "location": "Gurgaon, India", "industry": "Database", "is_indian_native": False},
    {"name": "Datadog India", "domain": "datadoghq.com", "careers_url": "https://www.datadoghq.com/careers", "platform": "greenhouse", "slug": "datadog", "location": "Bangalore, India", "industry": "Observability", "is_indian_native": False},
    {"name": "Rubrik India", "domain": "rubrik.com", "careers_url": "https://www.rubrik.com/company/careers", "platform": "greenhouse", "slug": "rubrik", "location": "Bangalore, India", "industry": "Data Security", "is_indian_native": False},
    {"name": "Cohesity India", "domain": "cohesity.com", "careers_url": "https://www.cohesity.com/company/careers", "platform": "greenhouse", "slug": "cohesity", "location": "Bangalore, India", "industry": "Data Management", "is_indian_native": False},
    {"name": "Zomato", "domain": "zomato.com", "careers_url": "https://www.zomato.com/careers", "platform": "greenhouse", "slug": "zomato", "location": "Gurugram, India", "industry": "FoodTech", "is_indian_native": True},
    {"name": "PhonePe", "domain": "phonepe.com", "careers_url": "https://www.phonepe.com/careers", "platform": "greenhouse", "slug": "phonepe", "location": "Bangalore, India", "industry": "Fintech", "is_indian_native": True},
]

INDIA_CITIES = [
    "india", "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "mumbai",
    "kolkata", "delhi", "ncr", "gurgaon", "gurugram", "noida", "ahmedabad",
    "jaipur", "indore", "kochi", "coimbatore", "chandigarh"
]

FOREIGN_TERMS = [
    "united states", "usa", "uk", "london", "dublin", "ireland", "singapore",
    "germany", "berlin", "canada", "toronto", "chicago", "san francisco", "austin",
    "new york", "seattle", "australia", "sydney", "tokyo", "japan", "brazil", "mexico"
]

def is_india_location(loc_str: str, is_indian_native: bool = False) -> bool:
    if not loc_str:
        return is_indian_native
    l = loc_str.lower()
    has_india = any(c in l for c in INDIA_CITIES)
    has_foreign = any(f in l for f in FOREIGN_TERMS)
    if has_india and not (has_foreign and "india" not in l):
        return True
    if is_indian_native and not has_foreign:
        return True
    if "remote" in l and not has_foreign and ("india" in l or "apac" in l or is_indian_native):
        return True
    return False

async def fetch_lever_jobs(client: httpx.AsyncClient, slug: str) -> List[Dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        r = await client.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

async def fetch_greenhouse_jobs(client: httpx.AsyncClient, slug: str) -> List[Dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        r = await client.get(url, timeout=15)
        if r.status_code == 200:
            return r.json().get("jobs", [])
    except Exception:
        pass
    return []

async def run():
    print("=" * 70)
    print("JOBPILOT AI — INDIA TECH ECOSYSTEM DISCOVERY")
    print(f"Targeting {len(INDIAN_COMPANIES)} premier Indian tech companies & high-growth startups...")
    print("=" * 70)

    db_path = "/Users/akash/Documents/autojob/backend/jobpilot_local.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Ensure company records exist
    for comp in INDIAN_COMPANIES:
        cur.execute("SELECT id FROM companies WHERE name = ?", (comp["name"],))
        row = cur.fetchone()
        if not row:
            cid = uuid.uuid4().hex
            cur.execute("""
                INSERT INTO companies (id, name, domain, careers_url, ats_platform, ats_identifier, location, industry, is_in_watchlist, is_verified, discovery_source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 'india_expansion', datetime('now'), datetime('now'))
            """, (cid, comp["name"], comp["domain"], comp["careers_url"], comp["platform"], comp["slug"], comp["location"], comp["industry"]))
        else:
            cur.execute("UPDATE companies SET ats_platform = ?, ats_identifier = ?, is_in_watchlist = 1 WHERE id = ?", (comp["platform"], comp["slug"], row[0]))
    conn.commit()

    total_scanned = 0
    total_india_jobs = 0

    headers = {"User-Agent": "JobPilot-AI-Agent/2.0 (Candidate Recruitment Intelligence; +https://jobpilot.ai)"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for comp in INDIAN_COMPANIES:
            cur.execute("SELECT id FROM companies WHERE name = ?", (comp["name"],))
            company_id = cur.fetchone()[0]

            print(f"-> Scanning {comp['name']} ({comp['platform']} / {comp['slug']})...", end=" ")
            jobs = []
            if comp["platform"] == "lever":
                jobs = await fetch_lever_jobs(client, comp["slug"])
            elif comp["platform"] == "greenhouse":
                jobs = await fetch_greenhouse_jobs(client, comp["slug"])

            company_india_jobs = 0
            for item in jobs:
                if comp["platform"] == "lever":
                    job_id = item.get("id")
                    title = item.get("text", "")
                    categories = item.get("categories", {})
                    location = categories.get("location", "") or ""
                    apply_url = item.get("hostedUrl", "")
                    description = item.get("descriptionPlain", "") or ""
                    commitment = categories.get("commitment", "Full-time")
                else:  # greenhouse
                    job_id = str(item.get("id"))
                    title = item.get("title", "")
                    location = item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else (item.get("location") or "")
                    apply_url = item.get("absolute_url", "")
                    description = item.get("content", "") or ""
                    commitment = "Full-time"

                if not is_india_location(location, comp.get("is_indian_native", False)):
                    continue

                if not location and comp.get("is_indian_native"):
                    location = comp.get("location", "Bangalore, India")

                clean_desc = re.sub(r'<[^>]+>', ' ', description)
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

                # Check duplicate
                cur.execute("SELECT id FROM jobs WHERE source = ? AND source_id = ?", (comp["platform"], str(job_id)))
                if cur.fetchone():
                    continue

                jid = uuid.uuid4().hex
                cur.execute("""
                    INSERT INTO jobs (id, company_id, source, source_id, title, description, location, location_type, employment_type, application_url, is_active, discovered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'onsite', ?, ?, 1, datetime('now'))
                """, (jid, company_id, comp["platform"], str(job_id), title, clean_desc[:4000], location, commitment, apply_url))

                company_india_jobs += 1
                total_india_jobs += 1

            conn.commit()
            print(f"found {len(jobs)} total jobs, {company_india_jobs} located in India")
            total_scanned += len(jobs)

    print("=" * 70)
    print(f"DISCOVERY COMPLETED: Scanned {total_scanned} total listings.")
    print(f"Newly added {total_india_jobs} verified India opportunities into the database!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run())
