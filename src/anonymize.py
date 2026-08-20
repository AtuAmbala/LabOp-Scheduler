import csv

INPUT = 'responses.csv'
OUTPUT = 'responses.csv'

with open(INPUT, mode='r', encoding='utf-8') as infile, \
        open(OUTPUT, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        print(row)
        row['Email'] = row.get('ID')
        row['Name'] = row.get('ID')
        row['Last name'] = row.get('ID')
        row['First name'] = row.get('ID')

        writer.writerow(row)