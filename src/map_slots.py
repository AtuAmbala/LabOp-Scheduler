import csv

BY_SLOT = 'v1_schedule/schedule_by_slot_v1.csv'
BY_STUDENT = 'v1_schedule/schedule_by_students_v1.csv'
BY_SLOT_OUTPUT = 'v1_schedule/schedule_by_slot_v1_output.csv'
BY_STUDENT_OUTPUT = 'v1_schedule/schedule_by_students_v1_output.csv'


def map_slot(input):
    if input[-1] == '2':
        day = "TUESDAY " + input[:-1]

    elif input[-1] == '3':
        day = "WEDNESDAY " + input[:-1]

    elif input[-1] == '4':
        day = "THURSDAY " + input[:-1]
                
    elif input[-1] == '5':
        day = "FRIDAY " + input[:-1]
                
    else:
        day = "MONDAY " + input
                
    return day

with open(BY_STUDENT, mode='r', encoding='utf-8') as infile, \
        open(BY_STUDENT_OUTPUT, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        row['slot 1'] = map_slot(str(row.get('slot 1')))
        row['slot 2'] = map_slot((str(row.get('slot 2'))))

        writer.writerow(row)


with open(BY_SLOT, mode='r', encoding='utf-8') as infile, \
        open(BY_SLOT_OUTPUT, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        row['slot'] = map_slot(str(row.get('slot')))
        writer.writerow(row)

