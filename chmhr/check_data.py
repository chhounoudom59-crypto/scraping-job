import csv

# Read and display the CSV data
with open('camhr_jobs_details.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
    print(f"Total rows: {len(rows)}")
    print("\nFirst job details:")
    if rows:
        for key, value in rows[0].items():
            if isinstance(value, str) and len(value) > 100:
                print(f"{key}: {value[:100]}...")
            else:
                print(f"{key}: {value}")
    
    # Count how many jobs have data (not N/A) for each field
    print("\n\nData completeness:")
    fields = list(rows[0].keys())
    for field in fields:
        count_with_data = sum(1 for row in rows if row[field] and row[field].strip() != "N/A")
        percentage = (count_with_data / len(rows)) * 100 if rows else 0
        print(f"{field}: {count_with_data}/{len(rows)} ({percentage:.1f}%)")
