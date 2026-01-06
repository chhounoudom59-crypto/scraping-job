# Jobify/main.py
import csv
import re
import time
from typing import Dict, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from detail import DETAIL_FIELDS, fetch_job_detail
from utils import BASE_URL, coalesce, make_session, polite_sleep

LIST_FIELDS = [
    "job_id",
    "slug",
    "title",
    "company",
    "location",
    "salary",
    "job_type",
    "posted_at",
    "url",
    "skills",
]


def _setup_driver(headless: bool = True) -> webdriver.Chrome:
    """Set up Chrome WebDriver for Selenium."""
    options = Options()
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
    )
    return driver


def _scrape_jobs_page(session) -> List[Dict]:
    """Scrape job listings from Jobify using Selenium to handle JavaScript rendering."""
    driver = _setup_driver(headless=True)
    jobs: List[Dict] = []
    seen = set()

    try:
        print("[INFO] Loading jobs page...")
        driver.get(f"{BASE_URL}/jobs")
        
        # Wait for page to load and jobs to appear
        # Try multiple selectors that might contain job links
        wait = WebDriverWait(driver, 20)
        
        # Wait for any job-related content to load
        try:
            # Look for job cards or links
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href*='/jobs/'], .job-card, [class*='job']")
                )
            )
        except TimeoutException:
            print("[WARN] No job elements found after waiting")
        
        # Give extra time for JavaScript to fully render
        time.sleep(3)
        
        # Target: Get 200 jobs
        target_jobs = 2000
        max_attempts = 100  # Maximum attempts to load more jobs (increased for pagination)
        attempt = 0
        current_page = 1
        
        while attempt < max_attempts:
            # Scroll to bottom first to trigger any lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Count current jobs
            soup = BeautifulSoup(driver.page_source, "html.parser")
            anchors = soup.select("a[href*='/jobs/']")
            if not anchors:
                anchors = soup.find_all("a", href=True)
                anchors = [a for a in anchors if "/jobs/" in a.get("href", "")]
            
            # Filter out navigation links
            job_links = []
            for a in anchors:
                href = a.get("href", "")
                if href and "/jobs/" in href and href not in ["/jobs", "/jobs/"]:
                    slug = href.split("/jobs/")[-1].strip("/").split("?")[0]
                    if slug and slug.isdigit():  # Only numeric slugs (job IDs)
                        job_links.append(slug)
            
            unique_jobs = len(set(job_links))
            print(f"[INFO] Attempt {attempt + 1}: Found {unique_jobs} unique jobs")
            
            if unique_jobs >= target_jobs:
                print(f"[INFO] Reached target of {target_jobs} jobs!")
                break
            
            # Try to find and click "Load More" button
            load_more_clicked = False
            try:
                # Try various selectors for Load More button
                load_more_selectors = [
                    "//button[contains(translate(., 'LOADMORE', 'loadmore'), 'load more')]",
                    "//button[contains(translate(., 'SHOWMORE', 'showmore'), 'show more')]",
                    "//button[contains(., 'More')]",
                    "//a[contains(., 'Load More')]",
                    "//button[@class and contains(@class, 'load')]",
                    "//button[@class and contains(@class, 'more')]",
                ]
                
                for selector in load_more_selectors:
                    try:
                        button = driver.find_element(By.XPATH, selector)
                        if button.is_displayed() and button.is_enabled():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", button)
                            print(f"[INFO] Clicked 'Load More' button")
                            load_more_clicked = True
                            time.sleep(3)  # Wait for new content to load
                            break
                    except:
                        continue
            except:
                pass
            
            # If no Load More button, try pagination
            if not load_more_clicked:
                try:
                    # Look for Vuetify pagination next button (chevron-right icon)
                    next_selectors = [
                        "//button[@class='v-pagination__navigation' and not(contains(@class, 'disabled'))]",
                        "//button[contains(@aria-label, 'Next page') and not(@disabled)]",
                        "//button[contains(@class, 'v-pagination__navigation') and not(contains(@class, 'disabled'))]",
                        "//i[contains(@class, 'mdi-chevron-right')]/ancestor::button[not(@disabled)]",
                    ]
                    
                    for selector in next_selectors:
                        try:
                            next_btn = driver.find_element(By.XPATH, selector)
                            if next_btn.is_displayed() and next_btn.is_enabled():
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", next_btn)
                                print(f"[INFO] Clicked pagination 'Next' button")
                                time.sleep(3)  # Wait for page to load
                                load_more_clicked = True
                                break
                        except:
                            continue
                    
                    # If next button not found, try clicking page numbers directly
                    if not load_more_clicked:
                        try:
                            # Find all page number buttons
                            page_buttons = driver.find_elements(By.CSS_SELECTOR, "button.v-pagination__item:not(.v-pagination__item--active)")
                            if page_buttons:
                                # Click the first non-active page button
                                next_page_btn = page_buttons[0]
                                if next_page_btn.is_displayed() and next_page_btn.is_enabled():
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_btn)
                                    time.sleep(1)
                                    driver.execute_script("arguments[0].click();", next_page_btn)
                                    page_num = next_page_btn.get_attribute("aria-label") or next_page_btn.text
                                    print(f"[INFO] Clicked page number button: {page_num}")
                                    time.sleep(3)
                                    load_more_clicked = True
                        except:
                            pass
                except:
                    pass
            
            # If still no new jobs loaded, try scrolling more
            if not load_more_clicked:
                # Try scrolling with longer wait
                last_height = driver.execute_script("return document.body.scrollHeight")
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            
            # Check if we got new jobs
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            new_anchors = soup.select("a[href*='/jobs/']")
            if not new_anchors:
                new_anchors = soup.find_all("a", href=True)
                new_anchors = [a for a in new_anchors if "/jobs/" in a.get("href", "")]
            
            new_job_links = []
            for a in new_anchors:
                href = a.get("href", "")
                if href and "/jobs/" in href and href not in ["/jobs", "/jobs/"]:
                    slug = href.split("/jobs/")[-1].strip("/").split("?")[0]
                    if slug and slug.isdigit():
                        new_job_links.append(slug)
            
            new_unique = len(set(new_job_links))
            if new_unique == unique_jobs and not load_more_clicked:
                # Check if we're on the last page
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, "button.v-pagination__navigation:not([disabled])")
                    if not next_btn or "disabled" in next_btn.get_attribute("class"):
                        print(f"[INFO] Reached last page. Total jobs: {new_unique}")
                        break
                except:
                    print(f"[INFO] No more pages available. Total jobs: {new_unique}")
                    break
            else:
                if load_more_clicked:
                    current_page += 1
                    print(f"[INFO] Now on page {current_page}, total unique jobs: {new_unique}")
            
            unique_jobs = new_unique
            attempt += 1
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Get final rendered HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find all job links
        anchors = soup.select("a[href*='/jobs/']")
        if not anchors:
            anchors = soup.find_all("a", href=True)
            anchors = [a for a in anchors if "/jobs/" in a.get("href", "")]
        
        print(f"[INFO] Final count: Found {len(anchors)} potential job links")
        
        for a in anchors:
            href = a.get("href")
            if not href:
                continue
            
            # Skip navigation links
            if href in ["/jobs", "/jobs/"]:
                continue
            
            # Normalize href (might be relative or absolute)
            if href.startswith("/"):
                full_url = BASE_URL + href
            elif href.startswith("http"):
                full_url = href
            else:
                full_url = f"{BASE_URL}/jobs/{href}"
            
            # Extract slug from href like /jobs/1234 or /jobs/slug-name
            if "/jobs/" in href:
                slug = href.split("/jobs/")[-1].strip("/").split("?")[0]
            else:
                continue
            
            # Only process numeric job IDs (skip if slug is not a number)
            if not slug or not slug.isdigit():
                continue
            
            if slug in seen:
                continue
            seen.add(slug)
            
            # Get title from link text or nearby elements
            title = coalesce(a.get_text(strip=True))
            if not title or len(title) < 5:
                # Try to find title in parent or sibling elements
                parent = a.find_parent()
                if parent:
                    title_elem = parent.find(["h1", "h2", "h3", "h4", "h5", ".title", "[class*='title']"])
                    if title_elem:
                        title = coalesce(title_elem.get_text(strip=True))
            
            # Try to extract additional info from the job card if available
            job_card = a.find_parent(["div", "article", "section"])
            company = ""
            location = ""
            salary = ""
            job_type = ""
            posted_at = ""
            skills = ""
            
            if job_card:
                # Try to find company name
                company_elem = job_card.find(["div", "span"], class_=lambda x: x and "company" in str(x).lower())
                if company_elem:
                    company = coalesce(company_elem.get_text(strip=True))
                
                # Try to find location
                location_elem = job_card.find(["div", "span"], class_=lambda x: x and "location" in str(x).lower())
                if location_elem:
                    location = coalesce(location_elem.get_text(strip=True))
                
                # Try to find salary
                salary_elem = job_card.find(["div", "span"], class_=lambda x: x and "salary" in str(x).lower())
                if salary_elem:
                    salary = coalesce(salary_elem.get_text(strip=True))
                
                # Try to find job type
                type_elem = job_card.find(["div", "span"], class_=lambda x: x and ("type" in str(x).lower() or "full" in str(x).lower() or "part" in str(x).lower()))
                if type_elem:
                    job_type = coalesce(type_elem.get_text(strip=True))
            
            jobs.append(
                {
                    "job_id": slug,
                    "slug": slug,
                    "title": title or "N/A",
                    "company": company,
                    "location": location,
                    "salary": salary,
                    "job_type": job_type,
                    "posted_at": posted_at,
                    "url": full_url,
                    "skills": skills,
                }
            )
        
        print(f"[INFO] Extracted {len(jobs)} unique jobs")
        
    finally:
        driver.quit()
    
    return jobs


def _save_csv(rows: List[Dict], path: str, fieldnames: List[str]) -> None:
    if not rows:
        print(f"[WARN] No rows to write for {path}")
        return
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Wrote {len(rows)} rows -> {path}")


def main() -> None:
    session = make_session()
    listings = _scrape_jobs_page(session)
    _save_csv(listings, "jobify_jobs_list.csv", LIST_FIELDS)

    if not listings:
        print("[INFO] No listings found; skipping detail scrape.")
        return

    detailed_rows: List[Dict] = []
    for idx, job in enumerate(listings, 1):
        try:
            detail = fetch_job_detail(session, "", job)  # no build_id needed
            detailed_rows.append(detail)
            print(f"[{idx}/{len(listings)}] OK {job['slug']}")
        except Exception as exc:
            print(f"[WARN] Failed {job['slug']}: {exc}")
        polite_sleep(1.5)

    if detailed_rows:
        _save_csv(detailed_rows, "jobify_jobs_detail.csv", DETAIL_FIELDS)


if __name__ == "__main__":
    main()