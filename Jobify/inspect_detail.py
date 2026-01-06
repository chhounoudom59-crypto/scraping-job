# Inspect a job detail page to see the HTML structure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def setup_driver():
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

driver = setup_driver()
try:
    url = "https://jobify.works/jobs/1183"
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for content
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)
    
    # Save HTML for inspection
    with open("inspect_detail.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Try to find title
    print("\n=== TITLE ===")
    for selector in ["h1", "h2", "h3", ".title", "[class*='title']", "[class*='Title']"]:
        elem = soup.select_one(selector)
        if elem:
            print(f"{selector}: {elem.get_text(strip=True)[:100]}")
    
    # Try to find company
    print("\n=== COMPANY ===")
    for selector in [".company", "[class*='company']", "[class*='Company']"]:
        elems = soup.select(selector)
        for elem in elems[:3]:
            print(f"{selector}: {elem.get_text(strip=True)[:100]}")
    
    # Try to find location
    print("\n=== LOCATION ===")
    for selector in [".location", "[class*='location']", "[class*='Location']"]:
        elems = soup.select(selector)
        for elem in elems[:3]:
            print(f"{selector}: {elem.get_text(strip=True)[:100]}")
    
    # Try to find salary
    print("\n=== SALARY ===")
    for selector in [".salary", "[class*='salary']", "[class*='Salary']"]:
        elems = soup.select(selector)
        for elem in elems[:3]:
            print(f"{selector}: {elem.get_text(strip=True)[:100]}")
    
    # Look for all text to understand structure
    print("\n=== ALL TEXT (first 2000 chars) ===")
    print(soup.get_text(separator="\n", strip=True)[:2000])
    
    print("\nHTML saved to inspect_detail.html")
    
finally:
    driver.quit()

