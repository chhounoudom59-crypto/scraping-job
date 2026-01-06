# Jobify/utils.py
import json
import time
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://jobify.works"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_json(session: requests.Session, url: str) -> Dict:
    resp = session.get(url, timeout=200)
    resp.raise_for_status()
    return resp.json()


def polite_sleep(seconds: float = 1.0) -> None:
    time.sleep(seconds)


def coalesce(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.strip()