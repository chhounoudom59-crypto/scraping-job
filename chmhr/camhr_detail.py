# camhr_detail.py
import csv
import re
import time
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

DETAIL_FIELDS = [
    "id", "title", "company", "industry", "location", "salary", "job_type",
    "experience", "education", "posting_date", "source", "description",
    "requirements", "url"
]

def _clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())[:200]

def scrape_job_detail(job: Dict, driver=None) -> Dict:
    """Scrape job detail from CamHR page using Selenium for client-side rendering."""
    close_driver = False
    
    if driver is None:
        # Create a new driver if not provided
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        driver = webdriver.Chrome(options=options)
        close_driver = True
    
    detail = {
        **job,
        "company": "N/A",
        "industry": "N/A",
        "location": "N/A",
        "salary": "N/A",
        "job_type": "N/A",
        "experience": "N/A",
        "education": "N/A",
        "posting_date": "N/A",
        "description": "N/A",
        "requirements": "N/A",
    }
    
    try:
        driver.get(job["url"])
        
        # Wait for job content to load - look for job-header-content class
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job-header-content"))
        )
        time.sleep(2)  # Extra wait for all content to render
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract company name - look for compnay-name class
        company_elem = soup.select_one(".compnay-name")
        if company_elem:
            detail["company"] = _clean_text(company_elem.get_text())
        
        # Extract location - look in company-info section for location-item
        location_items = soup.select(".location-item")
        if location_items:
            detail["location"] = _clean_text(location_items[0].get_text())
        
        # Extract salary - look for salary-fs-28 in job-title-content
        salary_elem = soup.select_one(".salary-fs-28")
        if salary_elem:
            detail["salary"] = _clean_text(salary_elem.get_text())
        
        # Extract description - look in job-descript section
        desc_elem = soup.select_one(".descript-list")
        if desc_elem:
            detail["description"] = _clean_text(desc_elem.get_text())[:500]
        
        # Look for structured fields in job-maininfo section
        # CamHR displays: "Label" followed by "Value" text
        job_maininfo = soup.select_one(".job-maininfo")
        if job_maininfo:
            # Get all text and split by common labels
            maininfo_text = job_maininfo.get_text()
            
            # Look for specific labels - they appear without colons in CamHR
            # Search for lines with labels like "Level", "Term", "Year of Exp.", etc.
            lines = [line.strip() for line in maininfo_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Job type / Term (Full Time, Part Time, etc)
                if "term" in line_lower and i + 1 < len(lines):
                    next_val = lines[i + 1]
                    if not any(kw in next_val.lower() for kw in ['company', 'profile', 'contact']):
                        detail["job_type"] = _clean_text(next_val)
                
                # Experience / Year of Exp
                if "year of exp" in line_lower and i + 1 < len(lines):
                    next_val = lines[i + 1]
                    if next_val and len(next_val) < 150 and not any(kw in next_val.lower() for kw in ['company', 'profile']):
                        detail["experience"] = _clean_text(next_val)
                
                # Education / Qualification
                if "qualification" in line_lower and i + 1 < len(lines):
                    next_val = lines[i + 1]
                    if next_val and len(next_val) < 100 and not any(kw in next_val.lower() for kw in ['company', 'profile']):
                        detail["education"] = _clean_text(next_val)
                
                # Industry
                if "industry" in line_lower and i + 1 < len(lines):
                    next_val = lines[i + 1]
                    if next_val and len(next_val) < 200 and not any(kw in next_val.lower() for kw in ['company', 'contact']):
                        detail["industry"] = _clean_text(next_val)
                
                # Posting date / Level
                if "level" in line_lower and i + 1 < len(lines):
                    next_val = lines[i + 1]
                    if next_val and len(next_val) < 100:
                        detail["posting_date"] = _clean_text(next_val)  # Use posting_date for level since we don't have actual date
        
        # Also check for divs with label:value format as fallback
        if not detail["job_type"] or detail["job_type"] == "N/A":
            for elem in soup.find_all(["div", "span"]):
                text = elem.get_text(strip=True)
                if "term" in text.lower() and ":" in text and len(text) < 100:
                    parts = text.split(":", 1)
                    if len(parts) == 2:
                        detail["job_type"] = _clean_text(parts[1])
        
        # Extract requirements - look for list items or detailed sections
        req_sections = soup.select(".job-descript")
        if len(req_sections) > 1:
            req_list = req_sections[1].select("li")
            if req_list:
                detail["requirements"] = "\n".join(
                    _clean_text(li.get_text()) for li in req_list[:5]
                )
            else:
                detail["requirements"] = _clean_text(req_sections[1].get_text())[:300]
        
    except Exception as e:
        print(f"Error scraping {job['url']}: {e}")
    
    finally:
        if close_driver and driver:
            driver.quit()
    
    # Convert empty strings to "N/A" for consistency
    for key in detail:
        if isinstance(detail[key], str) and not detail[key].strip():
            detail[key] = "N/A"
    
    return detail

def scrape_all_details(jobs: List[Dict], pause=1.5) -> List[Dict]:
    detailed = []
    
    # Use one driver instance to speed up scraping
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(options=options)
    
    try:
        for idx, job in enumerate(jobs, 1):
            try:
                print(f"Fetching job {idx}/{len(jobs)}: {job['id']}")
                detailed.append(scrape_job_detail(job, driver))
            except Exception as exc:
                print(f"⚠️  Failed job {job['id']}: {exc}")
            time.sleep(pause)
    finally:
        driver.quit()

    with open("camhr_jobs_details.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DETAIL_FIELDS)
        writer.writeheader()
        writer.writerows(detailed)

    print(f"Saved {len(detailed)} detailed jobs to camhr_jobs_details.csv")
    return detailed