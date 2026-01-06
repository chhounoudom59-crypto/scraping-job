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

from utils import BASE_URL, coalesce, fetch_json, make_session


DETAIL_FIELDS: List[str] = [
    "job_id",
    "slug",
    "title",
    "company",
    "salary",
    "job_type",
    "job_level",
    "experience",
    "education",
    "industry",
    "location",
    "language",
    "available_positions",
    "skills",
    "gender",
    "age",
    "published_at",
    "closing_at",
    "description",
    "requirements",
    "responsibilities",
    "how_to_apply",
    "url",
]


def _join_list(values) -> str:
    if isinstance(values, list):
        return ", ".join(item.strip() for item in values if item)
    return coalesce(values)


def _extract_text(block: Dict, key: str) -> str:
    value = block.get(key)
    if isinstance(value, list):
        cleaned = [item.strip() for item in value if item]
        return "\n".join(cleaned)
    return coalesce(value)


def _flatten_detail(job_payload: Dict, url: str) -> Dict:
    company_block = job_payload.get("company") or {}
    return {
        "job_id": job_payload.get("id"),
        "slug": job_payload.get("slug"),
        "title": coalesce(job_payload.get("title")),
        "company": coalesce(company_block.get("name")),
        "salary": coalesce(job_payload.get("salary")),
        "job_type": coalesce(job_payload.get("jobType")),
        "job_level": coalesce(job_payload.get("jobLevel")),
        "experience": coalesce(job_payload.get("experienceYears")),
        "education": coalesce(job_payload.get("qualification")),
        "industry": coalesce(job_payload.get("industry")),
        "location": coalesce(job_payload.get("location")),
        "language": coalesce(job_payload.get("language")),
        "available_positions": coalesce(job_payload.get("numberOfPositions")),
        "skills": _join_list(job_payload.get("skills") or []),
        "gender": coalesce(job_payload.get("genderRequirement")),
        "age": coalesce(job_payload.get("ageRequirement")),
        "published_at": coalesce(job_payload.get("publishedAt")),
        "closing_at": coalesce(job_payload.get("closingDate")),
        "description": _extract_text(job_payload, "jobDescription"),
        "requirements": _extract_text(job_payload, "jobRequirement"),
        "responsibilities": _extract_text(job_payload, "jobResponsibility"),
        "how_to_apply": _extract_text(job_payload, "howToApply"),
        "url": url,
    }


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


def _extract_label_value(soup: BeautifulSoup, label: str) -> str:
    """Extract value after a label like 'Salary:', 'Job Type:', etc."""
    # Find strong tag containing the label
    strong_tags = soup.find_all("strong")
    for strong in strong_tags:
        text = strong.get_text(strip=True)
        if label.lower() in text.lower():
            # Get the parent element and extract all text, then remove the label
            parent = strong.parent
            if parent:
                full_text = parent.get_text(strip=True)
                # Remove the label part
                value = full_text.replace(text, "", 1).strip()
                if value:
                    return value
            # Alternative: get next sibling text
            next_elem = strong.next_sibling
            if next_elem:
                value = str(next_elem).strip()
                if value:
                    return value
    return ""


def _scrape_html_fallback(session, slug: str) -> Dict:
    """Scrape job detail page using Selenium to handle JavaScript rendering."""
    detail_url = f"{BASE_URL}/jobs/{slug}"
    driver = _setup_driver(headless=True)
    
    try:
        driver.get(detail_url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 15)
        try:
            # Wait for job title to appear
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3"))
            )
        except TimeoutException:
            pass
        
        # Give extra time for JavaScript to render
        time.sleep(2)
        
        # Get rendered HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract title from h3 (main job title)
        title_elem = soup.select_one("h3")
        title_text = coalesce(title_elem.get_text(strip=True) if title_elem else "")
        
        # Extract fields using label-value pattern
        salary = _extract_label_value(soup, "Salary:")
        job_type = _extract_label_value(soup, "Job Type:")
        job_level = _extract_label_value(soup, "Job Level:")
        location = _extract_label_value(soup, "Location:")
        industry = _extract_label_value(soup, "Industry:")
        experience = _extract_label_value(soup, "Year of Experience:") or _extract_label_value(soup, "Experience:")
        education = _extract_label_value(soup, "Qualification:")
        # Extract language - it might be in a special format
        language = _extract_label_value(soup, "Language:")
        if not language:
            # Try to find language in a flex column format
            lang_elem = soup.find(lambda tag: "language" in tag.get_text(strip=True).lower()[:20])
            if lang_elem:
                # Get next sibling or parent text
                parent = lang_elem.find_parent()
                if parent:
                    text = parent.get_text(strip=True)
                    if "English" in text or "Khmer" in text:
                        # Extract language info
                        import re
                        match = re.search(r'(English|Khmer|Chinese|Japanese|Korean)[\s—\-]+(Advanced|Intermediate|Basic|Native)', text, re.IGNORECASE)
                        if match:
                            language = f"{match.group(1)} - {match.group(2)}"
        available_positions = _extract_label_value(soup, "Available Position:")
        gender = _extract_label_value(soup, "Gender:")
        age = _extract_label_value(soup, "Age:")
        published_at = _extract_label_value(soup, "Published date:")
        closing_at = _extract_label_value(soup, "Closing date:")
        
        # Extract skills
        skills_text = _extract_label_value(soup, "Required Skills:")
        skills_list = [s.strip() for s in skills_text.split(",") if s.strip()] if skills_text else []
        
        # Extract company name from __NUXT__ data or page
        company = ""
        # Try to extract from __NUXT__ script tag
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "company_name" in script.string:
                import re
                match = re.search(r'company_name["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string)
                if match:
                    company = match.group(1).strip()
                    break
        
        # If not found, try to find in page text
        if not company:
            # Look for company info in contact section or elsewhere
            company_elem = soup.find(lambda tag: tag.name in ("div", "span", "p") 
                                   and "company" in tag.get_text(strip=True).lower()[:30])
            if company_elem:
                text = company_elem.get_text(strip=True)
                # Try to extract company name pattern
                if ":" in text:
                    parts = text.split(":", 1)
                    if len(parts) > 1:
                        company = parts[1].strip()[:100]
        
        # Helper function to collect description sections
        def collect_section(label: str) -> str:
            # Find h5 heading with the label
            headers = soup.find_all("h5")
            header = None
            for h in headers:
                text = h.get_text(strip=True).lower()
                if label.lower() in text:
                    header = h
                    break
            
            if not header:
                return ""
            
            # Find the parent container (usually has class "job-content")
            parent_container = header.find_parent("div", class_=lambda x: x and "job-content" in str(x).lower())
            if not parent_container:
                parent_container = header.find_parent("div")
            
            # Get all content after this h5 until next h5
            content_parts = []
            current = header.find_next_sibling()
            
            depth = 0
            while current and depth < 30:
                # Stop at next h5 (another section)
                if current.name == "h5":
                    break
                
                # Get text from divs
                if current.name == "div":
                    classes = current.get("class", [])
                    class_str = " ".join(classes) if classes else ""
                    
                    # Look for divs with class "text-dark" or content divs
                    if "text-dark" in class_str or "content" in class_str.lower():
                        # Get all content inside this div
                        inner_divs = current.find_all("div", recursive=False)
                        if inner_divs:
                            for inner_div in inner_divs:
                                # Get paragraphs and lists
                                for elem in inner_div.find_all(["p", "ul", "ol"], recursive=False):
                                    if elem.name == "p":
                                        text = elem.get_text(strip=True)
                                        if text and len(text) > 5:
                                            content_parts.append(text)
                                    elif elem.name in ("ul", "ol"):
                                        items = [li.get_text(strip=True) for li in elem.find_all("li", recursive=False)]
                                        content_parts.extend([f"• {item}" for item in items if item])
                        else:
                            # Direct content in div
                            for elem in current.find_all(["p", "ul", "ol"], recursive=False):
                                if elem.name == "p":
                                    text = elem.get_text(strip=True)
                                    if text and len(text) > 5:
                                        content_parts.append(text)
                                elif elem.name in ("ul", "ol"):
                                    items = [li.get_text(strip=True) for li in elem.find_all("li", recursive=False)]
                                    content_parts.extend([f"• {item}" for item in items if item])
                elif current.name in ("ul", "ol"):
                    items = [li.get_text(strip=True) for li in current.find_all("li", recursive=False)]
                    content_parts.extend([f"• {item}" for item in items if item])
                elif current.name == "p":
                    text = current.get_text(strip=True)
                    if text and len(text) > 5:
                        content_parts.append(text)
                
                current = current.find_next_sibling()
                depth += 1
            
            # Clean up content
            cleaned = []
            for part in content_parts:
                part = part.strip()
                if part and len(part) > 3:
                    cleaned.append(part)
            
            return "\n".join(cleaned) if cleaned else ""
        
        description = collect_section("Job Description") or collect_section("Description")
        requirements = collect_section("Job Requirement") or collect_section("Requirement") or collect_section("Requirements")
        responsibilities = collect_section("Job Responsibility") or collect_section("Responsibility") or collect_section("Responsibilities")
        
        # Special handling for "How to apply" - it might be formatted differently
        how_to_apply = ""
        apply_headers = soup.find_all("h5")
        for h in apply_headers:
            text = h.get_text(strip=True).lower()
            if "how to apply" in text or "apply" in text:
                # Get the next div with class "text-dark"
                next_div = h.find_next_sibling("div")
                if next_div:
                    # Get all text content
                    apply_text = next_div.get_text(separator="\n", strip=True)
                    if apply_text:
                        how_to_apply = apply_text
                        break
                # If not found, try parent's next sibling
                parent = h.find_parent("div")
                if parent:
                    next_sibling = parent.find_next_sibling("div")
                    if next_sibling:
                        apply_text = next_sibling.get_text(separator="\n", strip=True)
                        if apply_text:
                            how_to_apply = apply_text
                            break
        
        # Fallback to collect_section if not found
        if not how_to_apply:
            how_to_apply = collect_section("How to apply") or collect_section("How to Apply") or collect_section("Apply")
        
        return {
            "id": slug,
            "slug": slug,
            "title": title_text,
            "company": {"name": company} if company else {},
            "salary": salary,
            "jobType": job_type,
            "jobLevel": job_level,
            "location": location,
            "industry": industry,
            "experienceYears": experience,
            "qualification": education,
            "language": language,
            "numberOfPositions": available_positions,
            "skills": skills_list,
            "genderRequirement": gender,
            "ageRequirement": age,
            "publishedAt": published_at,
            "closingDate": closing_at,
            "jobDescription": description,
            "jobRequirement": requirements,
            "jobResponsibility": responsibilities,
            "howToApply": how_to_apply,
        }
        
    finally:
        driver.quit()


def fetch_job_detail(session, build_id: str, job_row: Dict) -> Dict:
    """
    Fetch job detail from Jobify.
    Since this is a Nuxt.js app (not Next.js), we skip the API call and use HTML scraping.
    """
    slug = job_row["slug"]
    
    # Try HTML scraping directly (Nuxt.js doesn't use /_next/data/ endpoints)
    # If build_id is provided and not empty, we could try API, but for now use HTML
    job_payload = _scrape_html_fallback(session, slug)

    detail = _flatten_detail(job_payload, job_row["url"])
    # Ensure any empty-ish values stay blank, not whitespace
    for key, value in detail.items():
        if isinstance(value, str):
            detail[key] = value.strip()
    return detail