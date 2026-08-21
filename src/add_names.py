import csv

BY_SLOT = 'v1_schedule/schedule_by_slot_v1_output.csv'
BY_SLOT_OUTPUT = 'v1_schedule/schedule_by_slot_v1_output_new.csv'
BY_STUDENT = 'v1_schedule/schedule_by_students_v1_output.csv'
BY_STUDENT_OUTPUT = 'v1_schedule/schedule_by_students_v1_output_new.csv'


email_to_first_name = {}
email_to_last_name = {}

with open(BY_STUDENT, mode='r', encoding='utf-8') as infile, \
        open(BY_STUDENT_OUTPUT, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    print(reader.fieldnames)
    writer.writeheader()
    for row in reader:
        email_to_first_name[row.get('student_email')] = row.get('student_first_name')
        email_to_last_name[row.get('student_email')] = row.get('student_last_name')

with open(BY_SLOT, mode='r', encoding='utf-8') as infile, \
        open(BY_SLOT_OUTPUT, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    columns = reader.fieldnames
    print(reader.fieldnames)
    print(columns)
    columns.append('student_1_first_name')
    columns.append('student_1_last_name')
    columns.append('student_2_first_name')
    columns.append('student_2_last_name')
    
    writer = csv.DictWriter(outfile, fieldnames=columns)
    writer.writeheader()
    for row in reader:
        row['student_1_first_name'] = email_to_first_name[row.get('student 1')]
        row['student_1_last_name'] = email_to_last_name[row.get('student 1')]
        row['student_2_first_name'] = email_to_first_name[row.get('student 2')]
        row['student_2_last_name'] = email_to_last_name[row.get('student 2')]

        writer.writerow(row)
