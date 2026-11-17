"""
Ingest active India-specific engineering vacancies from verified Greenhouse and Lever boards,
score them with Akash's MCA/Fresher profile with strict India location filter, and reindex.
"""
import asyncio
import httpx
import sqlite3
import uuid
import re
from typing import List, Dict, Any
from app.agents.matching import matching_agent

ACTIVE_BOARDS = [
    {"name": "Okta India", "domain": "okta.com", "platform": "greenhouse", "slug": "okta", "location": "Bangalore, India", "industry": "Identity & Cloud Security"},
    {"name": "Zscaler India", "domain": "zscaler.com", "platform": "greenhouse", "slug": "zscaler", "location": "Bangalore / Pune, India", "industry": "Zero Trust Cloud Security"},
    {"name": "Stripe India", "domain": "stripe.com", "platform": "greenhouse", "slug": "stripe", "location": "Bangalore, India", "industry": "Global Fintech & Payment Infrastructure"},
    {"name": "InMobi", "domain": "inmobi.com", "platform": "greenhouse", "slug": "inmobi", "location": "Bangalore, India", "industry": "Mobile Advertising & AI Tech"},
    {"name": "Rubrik India", "domain": "rubrik.com", "platform": "greenhouse", "slug": "rubrik", "location": "Bangalore, India", "industry": "Enterprise Data Security"},
    {"name": "GitLab India", "domain": "gitlab.com", "platform": "greenhouse", "slug": "gitlab", "location": "Remote India", "industry": "DevSecOps & Software Delivery"},
    {"name": "Celonis India", "domain": "celonis.com", "platform": "greenhouse", "slug": "celonis", "location": "Bangalore, India", "industry": "Process Mining & Execution Management"},
    {"name": "Razorpay", "domain": "razorpay.com", "platform": "greenhouse", "slug": "razorpaysoftwareprivatelimited", "location": "Bangalore, India", "industry": "Fintech & Payment Gateway"},
    {"name": "MongoDB India", "domain": "mongodb.com", "platform": "greenhouse", "slug": "mongodb", "location": "Gurgaon / Bangalore, India", "industry": "Developer Data Platform"},
    {"name": "Elastic India", "domain": "elastic.co", "platform": "greenhouse", "slug": "elastic", "location": "Bangalore / Remote India", "industry": "Search & Observability AI"},
    {"name": "CRED", "domain": "cred.club", "platform": "lever", "slug": "cred", "location": "Bangalore, India", "industry": "Consumer Fintech & Rewards"},
    {"name": "Twilio India", "domain": "twilio.com", "platform": "greenhouse", "slug": "twilio", "location": "Bangalore, India", "industry": "Customer Engagement Platform"},
    {"name": "Airbnb India", "domain": "airbnb.com", "platform": "greenhouse", "slug": "airbnb", "location": "Bangalore / Gurgaon, India", "industry": "Marketplace & Travel Tech"},
    {"name": "Datadog India", "domain": "datadoghq.com", "platform": "greenhouse", "slug": "datadog", "location": "Bangalore, India", "industry": "Cloud Monitoring & APM"},
    {"name": "New Relic India", "domain": "newrelic.com", "platform": "greenhouse", "slug": "newrelic", "location": "Hyderabad / Bangalore, India", "industry": "Observability Platform"},
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

def is_india(loc: str) -> bool:
    if not loc:
        return False
    l = loc.lower()
    has_ind = any(c in l for c in INDIA_CITIES)
    has_for = any(f in l for f in FOREIGN_TERMS)
    return has_ind and not (has_for and "india" not in l)

async def fetch_jobs(client: httpx.AsyncClient, board: Dict[str, Any]) -> List[Dict[str, Any]]:
    plat = board["platform"]
    slug = board["slug"]
    if plat == "greenhouse":
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
        r = await client.get(url, timeout=12)
        if r.status_code == 200:
            return r.json().get("jobs", [])
    elif plat == "lever":
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        r = await client.get(url, timeout=12)
        if r.status_code == 200:
            return r.json()
    return []

async def main():
    db_path = "/Users/akash/Documents/autojob/backend/jobpilot_local.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Fetch Candidate
    cur.execute("SELECT id, full_name, email, experience_years FROM candidate_profiles LIMIT 1")
    cand = cur.fetchone()
    candidate_id = cand[0]
    candidate_dict = {"id": cand[0], "full_name": cand[1], "email": cand[2], "experience_years": cand[3]}

    cur.execute("SELECT fact_type, fact_data FROM candidate_facts WHERE candidate_id = ?", (candidate_id,))
    facts = [{"type": r[0], "data": eval(r[1]) if isinstance(r[1], str) else r[1]} for r in cur.fetchall()]

    print("Candidate loaded:", candidate_dict["full_name"], f"({len(facts)} verified facts)")

    # 2. Ingest India Jobs from Boards
    new_india_jobs = 0
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for b in ACTIVE_BOARDS:
            cur.execute("SELECT id FROM companies WHERE name = ?", (b["name"],))
            row = cur.fetchone()
            if not row:
                cid = uuid.uuid4().hex
                cur.execute("""
                    INSERT INTO companies (id, name, domain, careers_url, ats_platform, ats_identifier, location, industry, is_in_watchlist, is_verified, discovery_source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 'india_active', datetime('now'), datetime('now'))
                """, (cid, b["name"], b["domain"], f"https://{b['domain']}/careers", b["platform"], b["slug"], b["location"], b["industry"]))
                company_id = cid
            else:
                company_id = row[0]
                cur.execute("UPDATE companies SET ats_platform = ?, ats_identifier = ?, is_in_watchlist = 1 WHERE id = ?", (b["platform"], b["slug"], company_id))

            print(f"-> Fetching {b['name']} ({b['slug']})...", end=" ")
            try:
                raw_list = await fetch_jobs(client, b)
            except Exception as e:
                print(f"Error: {e}")
                continue

            ind_added = 0
            for item in raw_list:
                if b["platform"] == "greenhouse":
                    jid_str = str(item.get("id"))
                    title = item.get("title", "")
                    loc = item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else (item.get("location") or "")
                    apply_url = item.get("absolute_url", "")
                    content = item.get("content", "") or ""
                    dept = (item.get("departments") or [{}])[0].get("name", "Engineering")
                else:  # lever
                    jid_str = str(item.get("id"))
                    title = item.get("text", "")
                    loc = item.get("categories", {}).get("location", "") or ""
                    apply_url = item.get("hostedUrl", "")
                    content = item.get("descriptionPlain", "") or ""
                    dept = item.get("categories", {}).get("team", "Engineering")

                if not is_india(loc):
                    continue

                # Strip HTML
                clean_desc = re.sub(r'<[^>]+>', ' ', content)
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

                # Check duplicate
                cur.execute("SELECT id FROM jobs WHERE source = ? AND source_id = ?", (b["platform"], jid_str))
                existing_row = cur.fetchone()
                if existing_row:
                    job_uuid = existing_row[0]
                else:
                    job_uuid = uuid.uuid4().hex
                    cur.execute("""
                        INSERT INTO jobs (id, company_id, source, source_id, title, description, location, location_type, department, employment_type, application_url, is_active, discovered_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'onsite', ?, 'Full-time', ?, 1, datetime('now'))
                    """, (job_uuid, company_id, b["platform"], jid_str, title, clean_desc[:4000], loc, dept, apply_url))
                    new_india_jobs += 1
                    ind_added += 1

                # Match job with candidate
                match_res = await matching_agent.run({
                    "candidate": candidate_dict,
                    "candidate_facts": facts,
                    "job": {
                        "title": title,
                        "description": clean_desc,
                        "location": loc,
                        "required_skills": [],
                    },
                    "preferences": {"preferred_locations": INDIA_CITIES, "experience_years": 0.5}
                })

                if match_res["status"] == "success":
                    m = match_res["data"]
                    cur.execute("DELETE FROM job_matches WHERE job_id = ?", (job_uuid,))
                    mid = uuid.uuid4().hex
                    cur.execute("""
                        INSERT INTO job_matches (id, job_id, candidate_id, overall_score, skill_score, role_score, experience_score, location_score, salary_score, education_score, matched_skills, missing_skills, explanation, is_eligible, eligibility_notes, classification, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (mid, job_uuid, candidate_id, m["overall_score"], m["skill_score"], m["role_score"], m["experience_score"], m["location_score"], m["salary_score"], m["education_score"], str(m["matched_skills"]), str(m["missing_skills"]), m["explanation"], 1 if m["is_eligible"] else 0, m.get("eligibility_notes", ""), m["classification"]))

            conn.commit()
            print(f"found {len(raw_list)} postings, {ind_added} new India roles saved & matched.")

    # 3. Rescore ALL existing jobs in database with the new strict India location filter
    print("\nRescoring all previously discovered jobs in database with strict India filter...")
    cur.execute("SELECT id, title, description, location FROM jobs")
    all_jobs = cur.fetchall()
    
    rescored = 0
    strong_india_count = 0
    for jid, title, desc, loc in all_jobs:
        match_res = await matching_agent.run({
            "candidate": candidate_dict,
            "candidate_facts": facts,
            "job": {"title": title, "description": desc or "", "location": loc or "", "required_skills": []},
            "preferences": {"preferred_locations": INDIA_CITIES, "experience_years": 0.5}
        })
        if match_res["status"] == "success":
            m = match_res["data"]
            cur.execute("""
                UPDATE job_matches 
                SET overall_score = ?, skill_score = ?, role_score = ?, location_score = ?, is_eligible = ?, classification = ?, explanation = ?
                WHERE job_id = ?
            """, (m["overall_score"], m["skill_score"], m["role_score"], m["location_score"], 1 if m["is_eligible"] else 0, m["classification"], m["explanation"], jid))
            rescored += 1
            if m["overall_score"] >= 80 and m["is_eligible"]:
                strong_india_count += 1

    conn.commit()
    print(f"Rescored {rescored} jobs. Total strong India-specific matches (>=80%): {strong_india_count}")
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
