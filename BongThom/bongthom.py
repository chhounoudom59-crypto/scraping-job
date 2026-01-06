from bongthom_list import scrape_job_cards
from bongthom_detail import scrape_all_details

def main():
    basics = scrape_job_cards(max_scrolls=1500, delay=2.5)
    if not basics:
        print("No jobs collected — detail step skipped.")
        return
    scrape_all_details(basics)

if __name__ == "__main__":
    main()