from bongthom_detail import scrape_all_details
import csv

# Load existing jobs
with open('bongthom_jobs_list.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    jobs = list(reader)[:3]  # Test on first 3 jobs

print(f'Testing on {len(jobs)} jobs...')
for j in jobs:
    print(f"  - {j['id']}: {j['title'][:50]}")

scrape_all_details(jobs, pause=1)

# Show results
print("\n" + "="*80)
print("RESULTS:")
print("="*80)
with open('bongthom_jobs_details.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"\nID {row['id']}: {row['title'][:40]}")
        print(f"  Salary: {row['salary']}")
        print(f"  Industry: {row['industry']}")
        print(f"  Description: {row['description'][:70]}..." if len(row['description']) > 70 else f"  Description: {row['description']}")
        print(f"  Contact Email: {row['contact_email']}")
