# camhr_list.py
import csv
import re
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.camhr.com"
HOME_URL = BASE_URL + "/"
JOB_LINK_XPATH = "//a[contains(@href, '/job/') and not(contains(@href, 'jobwanted'))]"

def setup_driver(headless: bool = True) -> webdriver.Chrome:
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

def scrape_job_cards(max_clicks: int = 550, delay: float = 5.0):
    driver = setup_driver(headless=False)
    jobs, seen_ids = [], set()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(HOME_URL)
        wait.until(EC.presence_of_element_located((By.XPATH, JOB_LINK_XPATH)))

        for click in range(max_clicks):
            anchors = driver.find_elements(By.XPATH, JOB_LINK_XPATH)
            new_count = 0

            for anchor in anchors:
                href = anchor.get_attribute("href") or ""
                match = re.search(r"/job/(\d+)", href)
                if not match:
                    continue

                job_id = match.group(1)
                if job_id in seen_ids:
                    continue

                title = anchor.text.strip() or (
                    anchor.get_attribute("innerText") or ""
                ).strip()

                jobs.append(
                    {
                        "id": job_id,
                        "title": title or "N/A",
                        "url": urljoin(BASE_URL, href),
                        "source": "CamHR",
                    }
                )
                seen_ids.add(job_id)
                new_count += 1

            print(f"[{click + 1}/{max_clicks}] +{new_count} new jobs (total={len(jobs)})")
            if new_count == 0:
                break

            try:
                show_more = driver.find_element(
                    By.XPATH,
                    "//button[contains(translate(., 'LOADMORE', 'loadmore'), 'load more') "
                    "or contains(translate(., 'SHOWMORE', 'showmore'), 'show more')]",
                )
                driver.execute_script("arguments[0].click();", show_more)
            except Exception:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            try:
                wait.until(
                    lambda d: len(d.find_elements(By.XPATH, JOB_LINK_XPATH)) > len(anchors)
                )
            except TimeoutException:
                pass

            time.sleep(delay)

    finally:
        driver.quit()

    with open("camhr_jobs_list.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "url", "source"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"Saved {len(jobs)} job cards to camhr_jobs_list.csv")
    return jobs