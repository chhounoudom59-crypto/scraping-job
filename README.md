# 🕷️ scraping-job

A collection of web scrapers for Cambodia job sites.
This repository contains multiple scrapers that collect job listings and (where available) detailed job information, then export the results to CSV files.

---

## 📂 Project Structure

```
scraping-job/
│
├── Jobify/
│   ├── jobify_scraper.py
│   ├── requirements.txt
│   ├── jobify_jobs_list.csv
│   └── jobify_jobs_detail.csv
│
├── BongThom/
│   ├── bongthom_scraper.py
│   ├── bongthom_jobs_list.csv
│   └── bongthom_jobs_details.csv
│
├── chmhr/   # CamHR
│   ├── camhr_scraper.py
│   ├── camhr_jobs_list.csv
│   └── camhr_jobs_details.csv
│
└── README.md
```

### 🧩 Included Scrapers

#### 🟦 1. Jobify

* Website: [https://jobify.works](https://jobify.works)
* Tech stack: **Selenium** (Nuxt / dynamic site)
* Data collected:

  * Job list data
  * Job detail data
* Output files:

  * `jobify_jobs_list.csv`
  * `jobify_jobs_detail.csv`

#### 🟩 2. BongThom

* Website: [https://www.bongthom.com](https://www.bongthom.com)
* Tech stack: **Requests + BeautifulSoup + Selenium**
* Data collected:

  * Job list data
  * Job detail data
* Output files:

  * `bongthom_jobs_list.csv`
  * `bongthom_jobs_details.csv`

#### 🟨 3. CamHR (chmhr)

* Website: [https://www.camhr.com](https://www.camhr.com)
* Tech stack: **Selenium + BeautifulSoup**
* Data collected:

  * Job list data
  * Job detail data
* Output files:

  * `camhr_jobs_list.csv`
  * `camhr_jobs_details.csv`

---

## ⚙️ Requirements

* Python **3.10+** (recommended)
* Google Chrome (required for Selenium scrapers)
* Stable internet connection

### 📦 Python Packages

Common dependencies used in this repository:

* `requests`
* `beautifulsoup4`
* `selenium`
* `webdriver-manager`
* `fake-useragent` (optional)

> **Note:** The Jobify scraper has its own dependency file:
>
> `Jobify/requirements.txt`

---

## 🪟 Setup (Windows)

From the repository root directory:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -U pip
```

Install common dependencies:

```powershell
pip install requests beautifulsoup4 selenium webdriver-manager fake-useragent
```

For **Jobify only**, install its specific requirements:

```powershell
cd Jobify
pip install -r requirements.txt
cd ..
```

---

## ▶️ Usage

Run each scraper from its own folder.

### Jobify

```powershell
cd Jobify
python jobify_scraper.py
```

### BongThom

```powershell
cd BongThom
python bongthom_scraper.py
```

### CamHR

```powershell
cd chmhr
python camhr_scraper.py
```

After execution, CSV files will be generated in the same folder as the scraper.

---

## 📊 Output Format

Each CSV typically contains fields such as:

* Job title
* Company name
* Location
* Salary (if available)
* Job type
* Posted date
* Job description (detail scraper)
* Job URL

The exact columns may vary depending on the source website.

---

## 📝 Notes

* Selenium scrapers may take longer due to browser automation.
* Website structure changes may break scrapers.
* Use responsibly and respect each website’s **robots.txt** and **terms of service**.

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**.
The author is not responsible for misuse of the scraped data.

---

## 👤 Author

**CHHOUN Oudom**

GitHub: [https://github.com/chhounoudom59-crypto](https://github.com/chhounoudom59-crypto)
