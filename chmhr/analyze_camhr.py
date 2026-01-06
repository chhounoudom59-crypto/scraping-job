import csv

with open('camhr_jobs_details.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    jobs = list(reader)

# Show sample data
print('Sample CamHR jobs with data:')
print('=' * 100)
for i, job in enumerate(jobs[:5]):
    print(f"\n[{i+1}] ID: {job['id']} | Title: {job['title'][:50]}")
    print(f"    Company: {job['company']}")
    print(f"    Location: {job['location']}")
    print(f"    Salary: {job['salary']}")
    print(f"    Job Type: {job['job_type']}")
    print(f"    Description: {job['description'][:80]}..." if job['description'] != 'N/A' else f"    Description: N/A")

# Count fields with data
print(f"\n{'='*100}")
print(f"Statistics (out of {len(jobs)} jobs):")
companies = [j for j in jobs if j['company'] != 'N/A']
locations = [j for j in jobs if j['location'] != 'N/A']
salaries = [j for j in jobs if j['salary'] != 'N/A']
job_types = [j for j in jobs if j['job_type'] != 'N/A']
descs = [j for j in jobs if j['description'] != 'N/A']

print(f"  Jobs with company: {len(companies)} ({100*len(companies)/len(jobs):.1f}%)")
print(f"  Jobs with location: {len(locations)} ({100*len(locations)/len(jobs):.1f}%)")
print(f"  Jobs with salary: {len(salaries)} ({100*len(salaries)/len(jobs):.1f}%)")
print(f"  Jobs with job type: {len(job_types)} ({100*len(job_types)/len(jobs):.1f}%)")
print(f"  Jobs with description: {len(descs)} ({100*len(descs)/len(jobs):.1f}%)")
