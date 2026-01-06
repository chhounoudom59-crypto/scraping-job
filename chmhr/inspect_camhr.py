import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

url = "https://www.camhr.com/a/job/10641322?title=Project%20Engineer%20(%20SALE%20ENGINEER)"
resp = requests.get(url, headers=HEADERS, timeout=20)
soup = BeautifulSoup(resp.text, "html.parser")

# Save HTML for inspection
with open('debug_camhr.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

print("HTML saved to debug_camhr.html")

# Print all text content to see what's available
print("\n--- KEY CONTENT ---")
main_content = soup.select_one("main, [role='main'], .container, .content")
if main_content:
    text = main_content.get_text(separator="\n", strip=True)
    print(text[:1500])
else:
    print(soup.get_text(separator="\n", strip=True)[:1500])
