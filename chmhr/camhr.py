# camhr.py
from camhr_list import scrape_job_cards
from camhr_detail import scrape_all_details


def main():
    jobs = scrape_job_cards(max_clicks=550, delay=5)
    if not jobs:
        print("No jobs collected—detail step skipped.")
        return

    scrape_all_details(jobs)


if __name__ == "__main__":
    main()