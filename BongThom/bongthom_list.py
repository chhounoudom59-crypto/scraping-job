# bongthom_list.py
import csv
import os
import re
import time
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.bongthom.com"
JOBS_URL = f"{BASE_URL}/job_list.html"

CARD_LOCATORS = [
    (By.CSS_SELECTOR, "ul.bt-list.job-list > li"),  # BongThom main selector
    (By.CSS_SELECTOR, "div.job-item"),
    (By.CSS_SELECTOR, "div.job-card"),
    (By.CSS_SELECTOR, "li.job-item"),
    (By.XPATH, "//a[contains(@href,'/job_detail/')]"),
]

JOB_LINK_SELECTOR = "ul.bt-list.job-list > li a[href*='/job_detail/']"  # Updated for BongThom

LOAD_MORE_LOCATORS = [
    (By.XPATH, "//a[@class='page-link' and not(contains(@class,'disabled'))]//following::li[1]//a"),  # Next page button
    (By.CSS_SELECTOR, "li.page-item.page-next:not(.disabled) a.page-link"),  # Next pagination button
    (By.XPATH, "//button[contains(@class,'load-more') and not(@disabled)]"),
    (By.XPATH, "//button[contains(.,'Load More') and not(@disabled)]"),
]

IFRAME_LOCATORS = [
    (By.CSS_SELECTOR, "iframe#iframe-job-list"),
    (By.CSS_SELECTOR, "iframe[src*='job-list']"),
    (By.CSS_SELECTOR, "iframe[src*='/front/']"),
    (By.TAG_NAME, "iframe"),
]


def setup_driver(headless: bool = False) -> webdriver.Chrome:
    options = Options()
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
    )
    return driver


def _enter_job_frame(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    # Most modern websites don't use iframes for job listings
    # Check if job cards are available in main context
    print("[INFO] Checking for job cards in main page context...")
    
    # Wait for page to fully load and scripts to execute
    try:
        print("[INFO] Waiting for page to be ready...")
        # Wait for document.readyState to be complete
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print("[INFO] Document ready state: complete")
        
        # Extra wait for React/dynamic content
        time.sleep(3)
        
        # Wait for job list to be visible
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.bt-list.job-list")))
        print("[INFO] Job list container found")
        
    except TimeoutException:
        print("[WARNING] Timeout waiting for page readiness, continuing anyway...")
    except Exception as e:
        print(f"[WARNING] Error during page wait: {e}")
    
    # Just return - don't switch frames unless necessary
    return


def _wait_for_cards(wait: WebDriverWait, driver: webdriver.Chrome):
    # First try predefined locators
    for locator in CARD_LOCATORS:
        try:
            wait.until(EC.presence_of_all_elements_located(locator))
            print(f"[INFO] Found cards with locator: {locator}")
            return locator
        except TimeoutException:
            continue
    
    # If predefined locators fail, look for ANY clickable links with /job/ in href
    print("[WARNING] Standard selectors failed, searching for job links...")
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, JOB_LINK_SELECTOR)))
        print(f"[INFO] Found job links using fallback selector: {JOB_LINK_SELECTOR}")
        return (By.CSS_SELECTOR, JOB_LINK_SELECTOR)
    except TimeoutException:
        pass
    
    # Last resort: Dump page HTML to understand structure
    print("[WARNING] No job links found. Dumping page HTML for debugging...")
    try:
        html = driver.page_source
        # Save HTML for inspection
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[INFO] Page HTML saved to debug_page.html")
        
        # Look for common job listing patterns
        soup = BeautifulSoup(html, "html.parser")
        
        # Check for common job containers
        patterns = [
            ("div[class*='job']", "div with 'job' in class"),
            ("div[class*='listing']", "div with 'listing' in class"),
            ("div[class*='card']", "div with 'card' in class"),
            ("a[href*='job']", "links with 'job' in href"),
        ]
        
        for selector, desc in patterns:
            elements = soup.select(selector)
            if elements:
                print(f"[INFO] Found {len(elements)} elements matching '{desc}'")
                # Print first few
                for elem in elements[:3]:
                    text = elem.get_text(strip=True)[:100]
                    print(f"  - {elem.name}: {text}")
    except Exception as e:
        print(f"[ERROR] Failed to inspect page: {e}")
    
    raise TimeoutException("Job cards never appeared with known selectors.")


def _find_load_more(driver: webdriver.Chrome):
    # Try to find pagination next button or load more button
    for locator in LOAD_MORE_LOCATORS:
        try:
            element = driver.find_element(*locator)
            # Check if it's disabled or doesn't exist
            if "disabled" not in element.get_attribute("class"):
                return element
        except Exception:
            continue
    
    # Try to find next page button using a simpler approach
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "li.page-next:not(.disabled) a.page-link")
        return next_button
    except:
        pass
    
    return None


def _extract_job(anchor, seen_ids: set) -> Dict:
    try:
        href = anchor.get_attribute("href") or ""
        # Updated regex to match BongThom's URL pattern: /job_detail/..._ID.html
        match = re.search(r"/job_detail/.*_(\d+)\.html", href)
        if not match:
            # Try alternate pattern for older links
            match = re.search(r"/job/(\d+)", href)
        if not match:
            return {}
        job_id = match.group(1)
        if job_id in seen_ids:
            return {}

        # Get the parent list item
        try:
            li = anchor.find_element(By.XPATH, "./ancestor::li[1]")
            soup = BeautifulSoup(li.get_attribute("outerHTML"), "html.parser")
        except:
            soup = BeautifulSoup(anchor.get_attribute("outerHTML"), "html.parser")

        # Extract data from BongThom's structure
        # Title is in h5 tag inside span
        title_el = soup.select_one("h5 span") or soup.select_one("h5")
        # Company is in div.ellipsis-text after h5
        company_elements = soup.select("div.ellipsis-text")
        company_el = company_elements[0] if company_elements else None
        
        title = title_el.get_text(strip=True) if title_el else "N/A"
        company = company_el.get_text(strip=True) if company_el else "N/A"
        
        # For posted date, look for the clock icon info
        info_divs = soup.select("div.info")
        posted = "N/A"
        if info_divs:
            for info_div in info_divs:
                if "clock" in info_div.get_text() or "day" in info_div.get_text():
                    posted = info_div.get_text(strip=True)
                    break

        return {
            "id": job_id,
            "title": title,
            "company": company,
            "location": "N/A",  # BongThom doesn't show location in list view
            "posted_raw": "N/A",
            "url": href,
            "source": "BongThom",
        }
    except Exception as e:
        return {}


def scrape_job_cards(max_scrolls: int = 200, delay: float = 2.5) -> List[Dict]:
    driver = setup_driver(headless=False)
    wait = WebDriverWait(driver, 25)

    jobs: List[Dict] = []
    seen_ids: set = set()
    current_page = 1

    try:
        # Start from page 1
        page_url = f"{JOBS_URL}?page={current_page}"
        driver.get(page_url)
        print(f"[INFO] Navigating to {page_url}")
        _enter_job_frame(driver, wait)
        locator_used = _wait_for_cards(wait, driver)
        print(f"[INFO] Cards detected with locator: {locator_used}")

        last_total = 0
        stagnant_loops = 0

        for scroll in range(max_scrolls):
            # Find all li elements in the job list
            li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.bt-list.job-list > li")
            
            new_count = 0

            for li in li_elements:
                try:
                    # Get the anchor element inside the li
                    anchor = li.find_element(By.CSS_SELECTOR, "a[href*='/job_detail/']")
                    job = _extract_job(anchor, seen_ids)
                    if not job:
                        continue
                    seen_ids.add(job["id"])
                    job["url"] = urljoin(BASE_URL, job["url"].lstrip("/"))
                    jobs.append(job)
                    new_count += 1
                except Exception as e:
                    continue

            total = len(jobs)
            print(f"Scroll {scroll+1}/{max_scrolls} (Page {current_page}) — new {new_count} | total {total}")

            if total == last_total:
                stagnant_loops += 1
            else:
                stagnant_loops = 0
                last_total = total

            # Stop if truly no progress for multiple iterations
            if new_count == 0 and stagnant_loops >= 3:
                print("[INFO] No additional cards found on this page; moving to next page...")
                stagnant_loops = 0

            # Try to navigate to next page by clicking next button
            next_page_found = False
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "li.page-next:not(.disabled) a.page-link")
                if next_button:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_button)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    print(f"[INFO] Navigating to page {current_page}...")
                    next_page_found = True
                    
                    # Wait for page to load
                    time.sleep(delay + 1)
            except:
                pass
            
            # If no next button, try direct URL navigation
            if not next_page_found:
                current_page += 1
                page_url = f"{JOBS_URL}?page={current_page}"
                try:
                    print(f"[INFO] Loading page {current_page} directly from URL...")
                    driver.get(page_url)
                    time.sleep(delay + 1)
                    # Check if this page has content
                    li_test = driver.find_elements(By.CSS_SELECTOR, "ul.bt-list.job-list > li")
                    if not li_test:
                        print("[INFO] No more pages available; stopping.")
                        break
                except:
                    print("[INFO] Failed to load next page; stopping.")
                    break

    finally:
        driver.quit()

    if jobs:
        import tempfile
        import shutil
        
        # Use temp file to avoid permission issues
        temp_fd, temp_path = tempfile.mkstemp(suffix='.csv', text=True)
        try:
            with open(temp_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "id",
                        "title",
                        "company",
                        "location",
                        "posted_raw",
                        "url",
                        "source",
                    ],
                )
                writer.writeheader()
                writer.writerows(jobs)
            
            # Replace the original file with the temp file
            output_file = "bongthom_jobs_list.csv"
            if os.path.exists(output_file):
                os.remove(output_file)
            shutil.move(temp_path, output_file)
            print(f"[SUCCESS] Saved {len(jobs)} jobs to {output_file}")
        except Exception as e:
            print(f"[ERROR] Failed to write CSV: {e}")
            # At least try to close the temp file
            try:
                os.close(temp_fd)
            except:
                pass
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    else:
        print("[INFO] No jobs collected")

    print(f"[DONE] Saved {len(jobs)} job cards to bongthom_jobs_list.csv")
    return jobs