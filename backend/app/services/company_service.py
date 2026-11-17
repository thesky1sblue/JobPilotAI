from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.jobs import Company

INITIAL_COMPANIES = [
    {"name": "Google", "domain": "google.com", "careers_url": "https://careers.google.com", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "Technology"},
    {"name": "Microsoft", "domain": "microsoft.com", "careers_url": "https://careers.microsoft.com", "ats_platform": "custom", "ats_identifier": None, "location": "Hyderabad, India", "industry": "Technology"},
    {"name": "Amazon", "domain": "amazon.com", "careers_url": "https://www.amazon.jobs", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "Technology"},
    {"name": "Meta", "domain": "meta.com", "careers_url": "https://www.metacareers.com", "ats_platform": "custom", "ats_identifier": None, "location": "Remote", "industry": "Technology"},
    {"name": "Apple", "domain": "apple.com", "careers_url": "https://jobs.apple.com", "ats_platform": "custom", "ats_identifier": None, "location": "Remote", "industry": "Technology"},
    {"name": "Flipkart", "domain": "flipkart.com", "careers_url": "https://www.flipkartcareers.com", "ats_platform": "greenhouse", "ats_identifier": "flipkart", "location": "Bangalore, India", "industry": "E-commerce"},
    {"name": "Swiggy", "domain": "swiggy.com", "careers_url": "https://careers.swiggy.com", "ats_platform": "lever", "ats_identifier": "swiggy", "location": "Bangalore, India", "industry": "Food Tech"},
    {"name": "Zomato", "domain": "zomato.com", "careers_url": "https://www.zomato.com/careers", "ats_platform": "greenhouse", "ats_identifier": "zomato", "location": "Gurugram, India", "industry": "Food Tech"},
    {"name": "Razorpay", "domain": "razorpay.com", "careers_url": "https://razorpay.com/jobs", "ats_platform": "lever", "ats_identifier": "razorpay", "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "CRED", "domain": "cred.club", "careers_url": "https://careers.cred.club", "ats_platform": "lever", "ats_identifier": "cred", "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "PhonePe", "domain": "phonepe.com", "careers_url": "https://www.phonepe.com/careers", "ats_platform": "greenhouse", "ats_identifier": "phonepe", "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "Paytm", "domain": "paytm.com", "careers_url": "https://paytm.com/careers", "ats_platform": "custom", "ats_identifier": None, "location": "Noida, India", "industry": "Fintech"},
    {"name": "Infosys", "domain": "infosys.com", "careers_url": "https://careers.infosys.com", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "IT Services"},
    {"name": "TCS", "domain": "tcs.com", "careers_url": "https://www.tcs.com/careers", "ats_platform": "custom", "ats_identifier": None, "location": "Mumbai, India", "industry": "IT Services"},
    {"name": "Wipro", "domain": "wipro.com", "careers_url": "https://careers.wipro.com", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "IT Services"},
    {"name": "HCL Technologies", "domain": "hcltech.com", "careers_url": "https://www.hcltech.com/careers", "ats_platform": "custom", "ats_identifier": None, "location": "Noida, India", "industry": "IT Services"},
    {"name": "Tech Mahindra", "domain": "techmahindra.com", "careers_url": "https://careers.techmahindra.com", "ats_platform": "custom", "ats_identifier": None, "location": "Pune, India", "industry": "IT Services"},
    {"name": "Adobe", "domain": "adobe.com", "careers_url": "https://www.adobe.com/careers.html", "ats_platform": "greenhouse", "ats_identifier": "adobe", "location": "Bangalore, India", "industry": "Software"},
    {"name": "Salesforce", "domain": "salesforce.com", "careers_url": "https://careers.salesforce.com", "ats_platform": "custom", "ats_identifier": None, "location": "Hyderabad, India", "industry": "CRM"},
    {"name": "Oracle", "domain": "oracle.com", "careers_url": "https://www.oracle.com/careers", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "Technology"},
    {"name": "SAP", "domain": "sap.com", "careers_url": "https://jobs.sap.com", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "Enterprise Software"},
    {"name": "Nvidia", "domain": "nvidia.com", "careers_url": "https://www.nvidia.com/en-us/about-nvidia/careers", "ats_platform": "greenhouse", "ats_identifier": "nvidia", "location": "Bangalore, India", "industry": "Semiconductors"},
    {"name": "Uber", "domain": "uber.com", "careers_url": "https://www.uber.com/global/en/careers", "ats_platform": "greenhouse", "ats_identifier": "uber", "location": "Bangalore, India", "industry": "Transportation"},
    {"name": "Stripe", "domain": "stripe.com", "careers_url": "https://stripe.com/jobs", "ats_platform": "greenhouse", "ats_identifier": "stripe", "location": "Remote", "industry": "Fintech"},
    {"name": "Atlassian", "domain": "atlassian.com", "careers_url": "https://www.atlassian.com/company/careers", "ats_platform": "greenhouse", "ats_identifier": "atlassian", "location": "Remote", "industry": "Software"},
    {"name": "Freshworks", "domain": "freshworks.com", "careers_url": "https://www.freshworks.com/company/careers", "ats_platform": "greenhouse", "ats_identifier": "freshworks", "location": "Chennai, India", "industry": "SaaS"},
    {"name": "Zoho", "domain": "zoho.com", "careers_url": "https://careers.zoho.com", "ats_platform": "custom", "ats_identifier": None, "location": "Chennai, India", "industry": "SaaS"},
    {"name": "Byju's", "domain": "byjus.com", "careers_url": "https://byjus.com/careers", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "EdTech"},
    {"name": "Unacademy", "domain": "unacademy.com", "careers_url": "https://unacademy.com/careers", "ats_platform": "lever", "ats_identifier": "unacademy", "location": "Bangalore, India", "industry": "EdTech"},
    {"name": "Meesho", "domain": "meesho.com", "careers_url": "https://meesho.io/careers", "ats_platform": "greenhouse", "ats_identifier": "meesho", "location": "Bangalore, India", "industry": "E-commerce"},
    {"name": "ShareChat", "domain": "sharechat.com", "careers_url": "https://careers.sharechat.com", "ats_platform": "greenhouse", "ats_identifier": "sharechat", "location": "Bangalore, India", "industry": "Social Media"},
    {"name": "Groww", "domain": "groww.in", "careers_url": "https://careers.groww.in", "ats_platform": "lever", "ats_identifier": "groww", "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "Zerodha", "domain": "zerodha.com", "careers_url": "https://zerodha.com/careers", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "BrowserStack", "domain": "browserstack.com", "careers_url": "https://www.browserstack.com/careers", "ats_platform": "greenhouse", "ats_identifier": "browserstack", "location": "Mumbai, India", "industry": "DevTools"},
    {"name": "Postman", "domain": "postman.com", "careers_url": "https://www.postman.com/company/careers", "ats_platform": "greenhouse", "ats_identifier": "postman", "location": "Bangalore, India", "industry": "DevTools"},
    {"name": "Druva", "domain": "druva.com", "careers_url": "https://www.druva.com/company/careers", "ats_platform": "greenhouse", "ats_identifier": "druva", "location": "Pune, India", "industry": "Cloud"},
    {"name": "Darwinbox", "domain": "darwinbox.com", "careers_url": "https://darwinbox.com/careers", "ats_platform": "greenhouse", "ats_identifier": "darwinbox", "location": "Hyderabad, India", "industry": "HR Tech"},
    {"name": "LeadSquared", "domain": "leadsquared.com", "careers_url": "https://www.leadsquared.com/careers", "ats_platform": "greenhouse", "ats_identifier": "leadsquared", "location": "Bangalore, India", "industry": "CRM"},
    {"name": "Clevertap", "domain": "clevertap.com", "careers_url": "https://clevertap.com/careers", "ats_platform": "greenhouse", "ats_identifier": "clevertap", "location": "Mumbai, India", "industry": "MarTech"},
    {"name": "Capillary Technologies", "domain": "capillarytech.com", "careers_url": "https://www.capillarytech.com/careers", "ats_platform": "greenhouse", "ats_identifier": "capillary", "location": "Bangalore, India", "industry": "Retail Tech"},
    {"name": "Setu", "domain": "setu.co", "careers_url": "https://setu.co/careers", "ats_platform": "lever", "ats_identifier": "setu", "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "smallcase", "domain": "smallcase.com", "careers_url": "https://careers.smallcase.com", "ats_platform": "lever", "ats_identifier": "smallcase", "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "Jupiter", "domain": "jupiter.money", "careers_url": "https://jupiter.money/careers", "ats_platform": "lever", "ats_identifier": "jupiter-money", "location": "Mumbai, India", "industry": "Fintech"},
    {"name": "Navi", "domain": "navi.com", "careers_url": "https://navi.com/careers", "ats_platform": "lever", "ats_identifier": "navi", "location": "Bangalore, India", "industry": "Fintech"},
    {"name": "Qualcomm", "domain": "qualcomm.com", "careers_url": "https://www.qualcomm.com/company/careers", "ats_platform": "custom", "ats_identifier": None, "location": "Hyderabad, India", "industry": "Semiconductors"},
    {"name": "Intel", "domain": "intel.com", "careers_url": "https://jobs.intel.com", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "Semiconductors"},
    {"name": "VMware", "domain": "vmware.com", "careers_url": "https://careers.vmware.com", "ats_platform": "greenhouse", "ats_identifier": "vmware", "location": "Bangalore, India", "industry": "Cloud"},
    {"name": "SAP Labs", "domain": "sap.com", "careers_url": "https://jobs.sap.com", "ats_platform": "custom", "ats_identifier": None, "location": "Bangalore, India", "industry": "Enterprise Software"},
    {"name": "Airbnb", "domain": "airbnb.com", "careers_url": "https://careers.airbnb.com", "ats_platform": "greenhouse", "ats_identifier": "airbnb", "location": "Remote", "industry": "Travel"},
    {"name": "Hasura", "domain": "hasura.io", "careers_url": "https://hasura.io/careers", "ats_platform": "lever", "ats_identifier": "hasura", "location": "Bangalore, India", "industry": "Database"},
]

async def seed_initial_companies(db: AsyncSession) -> int:
    added = 0
    for data in INITIAL_COMPANIES:
        result = await db.execute(select(Company).where(Company.name == data["name"]))
        if not result.scalar_one_or_none():
            company = Company(**data, is_in_watchlist=True, is_verified=True, discovery_source="seed")
            db.add(company)
            added += 1
    await db.commit()
    return added
