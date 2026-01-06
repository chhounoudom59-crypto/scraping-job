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
    
    # Find all text content with ":" to see what labels exist
    with open('page_labels.txt', 'w', encoding='utf-8') as f:
        f.write("=== ALL LABEL:VALUE PAIRS FOUND ===\n\n")
        
        for elem in soup.find_all(["div", "p", "span"]):
            text = elem.get_text(strip=True)
            if ":" in text and len(text) < 300 and len(text) > 5:
                f.write(text + "\n\n")
    
    print("Saved page labels to page_labels.txt")

finally:
    driver.quit()
