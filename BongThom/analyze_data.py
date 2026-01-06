import csv

with open('bongthom_jobs_details.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    jobs = list(reader)

# Show variety of data
print('Sample jobs with data:')
print('=' * 100)
for i, job in enumerate(jobs[:5]):
    print(f"\n[{i+1}] ID: {job['id']} | Title: {job['title'][:50]}")
    print(f"    Salary: {job['salary']}")
    print(f"    Industry: {job['industry']}")
    print(f"    Email: {job['contact_email']}")
    print(f"    Phone: {job['contact_phone']}")
    print(f"    Desc: {job['description'][:80] if job['description'] != 'N/A' else 'N/A'}...")

# Count fields with data
print(f"\n{'='*100}")
print(f"Statistics (out of {len(jobs)} jobs):")
salaries = [j for j in jobs if j['salary'] != 'N/A']
emails = [j for j in jobs if j['contact_email'] != 'N/A']
phones = [j for j in jobs if j['contact_phone'] != 'N/A']
descs = [j for j in jobs if j['description'] != 'N/A']

print(f"  Jobs with salary: {len(salaries)} ({100*len(salaries)/len(jobs):.1f}%)")
print(f"  Jobs with email: {len(emails)} ({100*len(emails)/len(jobs):.1f}%)")
print(f"  Jobs with phone: {len(phones)} ({100*len(phones)/len(jobs):.1f}%)")
print(f"  Jobs with description: {len(descs)} ({100*len(descs)/len(jobs):.1f}%)")
