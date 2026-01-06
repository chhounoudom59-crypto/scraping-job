from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup

url = "https://www.camhr.com/a/job/10644891"

options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
driver = webdriver.Chrome(options=options)

try:
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "job-header-content"))
    )
    time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Find the job-maininfo section specifically
    job_maininfo = soup.select_one(".job-maininfo")
    if job_maininfo:
        with open('job_maininfo.txt', 'w', encoding='utf-8') as f:
            f.write("=== JOB MAININFO SECTION ===\n\n")
            
            # Get all divs with both text and structure
            for div in job_maininfo.find_all("div", recursive=True)[:30]:
                text = div.get_text(strip=True)
                if text and len(text) < 300:
                    f.write(f"{text}\n---\n")
        
        print("Saved job_maininfo to job_maininfo.txt")

finally:
    driver.quit()
