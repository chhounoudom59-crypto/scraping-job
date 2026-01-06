# bongthom_detail.py
import csv
import time
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

DETAIL_FIELDS = [
    "id",
    "title",
    "company",
    "industry",
    "location",
    "salary",
    "employment_type",
    "experience",
    "education",
    "posted_date",
    "closing_date",
    "contact_email",
    "contact_phone",
    "apply_instructions",
    "description",
    "requirements",
    "url",
    "source",
]


def _clean_text(node) -> str:
    if not node:
        return "N/A"
    return node.get_text(separator="\n", strip=True)


def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def scrape_job_detail(job: Dict, session: requests.Session) -> Dict:
    url = job["url"]
    resp = session.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Start with only the fields we need from the job dict
    detail = {
        "id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "url": job.get("url"),
        "source": job.get("source", "BongThom"),
        "industry": "",
        "salary": "",
        "employment_type": "",
        "experience": "",
        "education": "",
        "posted_date": job.get("posted_raw", ""),
        "closing_date": "",
        "contact_email": "",
        "contact_phone": "",
        "apply_instructions": "",
        "description": "",
        "requirements": "",
        "location": job.get("location", ""),
    }

    # Try to find info rows in multiple common formats
    # Look for divs or spans containing job info
    all_text_content = soup.get_text()
    
    # Try common selectors for job details
    info_rows = soup.select("div[class*='info'], tr, .job-info, .job-information, li, p")
    
    for row in info_rows:
        text = row.get_text(strip=True).lower()
        
        # Extract field-value pairs from common patterns
        if "industry" in text:
            match_text = row.get_text(separator=" ", strip=True)
            parts = match_text.split(":", 1)
            if len(parts) == 2:
                detail["industry"] = parts[1].strip() or detail["industry"]
                
        elif "salary" in text or "income" in text:
            match_text = row.get_text(separator=" ", strip=True)
            parts = match_text.split(":", 1)
            if len(parts) == 2:
                detail["salary"] = parts[1].strip() or detail["salary"]
                
        elif ("employment" in text or "type of employment" in text) and "N/A" not in text.lower():
            match_text = row.get_text(separator=" ", strip=True)
            parts = match_text.split(":", 1)
            if len(parts) == 2:
                detail["employment_type"] = parts[1].strip() or detail["employment_type"]
                
        elif "experience" in text and "require" in text:
            match_text = row.get_text(separator=" ", strip=True)
            parts = match_text.split(":", 1)
            if len(parts) == 2:
                detail["experience"] = parts[1].strip() or detail["experience"]
                
        elif "education" in text or "qualification" in text:
            match_text = row.get_text(separator=" ", strip=True)
            parts = match_text.split(":", 1)
            if len(parts) == 2:
                detail["education"] = parts[1].strip() or detail["education"]
                
        elif ("closing" in text or "deadline" in text or "closing date" in text):
            match_text = row.get_text(separator=" ", strip=True)
            parts = match_text.split(":", 1)
            if len(parts) == 2:
                detail["closing_date"] = parts[1].strip() or detail["closing_date"]

    # Try to find description (look for longer paragraphs)
    potential_desc = soup.select("p, div[class*='description'], div[class*='detail'], div[class*='content']")
    if potential_desc:
        for elem in potential_desc:
            desc_text = _clean_text(elem)
            if len(desc_text) > 50 and "N/A" not in desc_text:  # Get longer content
                detail["description"] = desc_text
                break

    # Try to find requirements
    req_sections = soup.select("ul, ol")
    if req_sections:
        for req_section in req_sections:
            lis = [li.get_text(strip=True) for li in req_section.select("li")]
            if lis and len(lis) > 0:
                detail["requirements"] = "\n".join(lis[:10])  # First 10 items max
                break

    # Try to find contact info (emails and phones)
    all_links = soup.select("a[href^='mailto:'], a[href^='tel:']")
    for link in all_links:
        href = link.get("href", "").lower()
        text = link.get_text(strip=True)
        if "mailto:" in href and not detail["contact_email"]:
            detail["contact_email"] = text or href.replace("mailto:", "")
        elif "tel:" in href and not detail["contact_phone"]:
            detail["contact_phone"] = text or href.replace("tel:", "")

    # Convert empty strings back to "N/A" for consistency
    for key in detail:
        if detail[key] == "":
            detail[key] = "N/A"

    return detail


def scrape_all_details(jobs: List[Dict], pause: float = 1.5) -> List[Dict]:
    session = _make_session()
    detailed: List[Dict] = []

    try:
        for idx, job in enumerate(jobs, 1):
            print(f"[{idx}/{len(jobs)}] Fetching job {job['id']}")
            try:
                detail = scrape_job_detail(job, session)
                detailed.append(detail)
            except Exception as exc:
                print(f"  [WARN] Failed {job['id']}: {exc}")
            time.sleep(pause)
    finally:
        session.close()

    with open("bongthom_jobs_details.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DETAIL_FIELDS)
        writer.writeheader()
        writer.writerows(detailed)

    print(f"[DONE] Saved {len(detailed)} detailed jobs to bongthom_jobs_details.csv")
    return detailed