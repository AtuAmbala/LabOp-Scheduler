import csv
import sys
import re
from collections import defaultdict

AVAILABILITY_CSV = 'LabOp Timeslot Preference Selection Form - Filled.csv'
STUDENT_SCHEDULE_CSV = 'LabOp_Student_Schedule.csv'

AVAILABILITY_MAP = {'MUST-SELECT': 'MUST', 'CANNOT-SELECT': 'CANNOT', 'OK': 'OK'}


def normalize_name(n: str) -> str:
    if not n:
        return ''
    s = re.sub(r'\s+', ' ', str(n).strip())
    return s.lower()


def normalize_slot(s: str) -> str:
    if not s:
        return ''
    x = str(s).upper()
    x = x.replace('12 NOON', '12 PM')
    x = re.sub(r'\s+', ' ', x).strip()
    return x.lower()

def read_availability(filepath):
    with open(filepath, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return {}
    header_row = None
    for r in rows[:5]:
        if any(h and h.strip().lower() in ('name', '\ufeffname', 'first name', 'first', 'student') for h in r):
            header_row = r
            break
    if header_row is None:
        header_row = rows[0]

    LAB_HOURS = [('Monday',9,21),('Tuesday',9,21),('Wednesday',9,21),('Thursday',9,21),('Friday',9,16),('Saturday',12,16),('Sunday',12,17)]
    def fmt_label(h):
        if h==12: return '12 PM'
        if h==0 or h==24: return '12 AM'
        if h<12: return f"{h} AM"
        return f"{h-12} PM"
    canonical_slots=[]
    for day,start,end in LAB_HOURS:
        for h in range(start,end): canonical_slots.append(f"{day} {fmt_label(h)} - {fmt_label(h+1)}")
    header_cols = header_row
    mapped_slots = []
    slot_cols = []
    for col in header_cols[1:]:
        if col is None:
            mapped_slots.append(None)
            continue
        key = col.strip()
        if key.lower().startswith('slot'):
            slot_cols.append(key)
            mapped_slots.append(None)  
            continue
        mapped_slots.append(key)
    if slot_cols:
        indices = [i for i,c in enumerate(header_cols[1:]) if c and str(c).strip().lower().startswith('slot')]
        for k, idx in enumerate(indices):
            if k < len(canonical_slots):
                mapped_slots[idx] = canonical_slots[k]

    student_map = {}
    start_idx = rows.index(header_row) + 1
    for row in rows[start_idx:]:
        if not row: continue
        try:
            row_map = {h: (row[i] if i < len(row) else '') for i,h in enumerate(header_cols)}
        except Exception:
            row_map = {}
        name = ''
        if 'First name' in header_cols and 'Last name' in header_cols:
            try:
                fn = row_map.get('First name','').strip()
                ln = row_map.get('Last name','').strip()
                name = (fn + ' ' + ln).strip()
            except:
                name = ''
        if not name and 'Name' in header_cols:
            name = (row_map.get('Name','') or '').strip()
        if not name and 'Email' in header_cols:
            name = (row_map.get('Email','') or '').strip()
        if not name:
            for v in row:
                if v and v.strip():
                    name = v.strip(); break
        if not name: continue
        name_key = normalize_name(name)
        availability = {}
        for i,slot in enumerate(mapped_slots):
            val = ''
            try:
                val = row[1+i].strip()
            except:
                val = ''
            code = AVAILABILITY_MAP.get(val.upper(),'OK') if val else 'OK'
            if slot:
                availability[normalize_slot(slot)] = code
        student_map[name_key] = availability
    return student_map


def read_student_schedule(filepath):
    smap={}
    with open(filepath, newline='') as f:
        reader=csv.DictReader(f)
        for r in reader:
            student=(r.get('Student') or '').strip()
            if not student: continue
            student_key = normalize_name(student)
            slots=[]
            for k in list(r.keys()):
                if k and k.startswith('Hour'):
                    v=(r.get(k) or '').strip()
                    if v:
                        sv = v.upper().replace('12 NOON','12 PM')
                        sv = re.sub(r'\s+', ' ', sv).strip().lower()
                        slots.append(sv)
            smap[student_key]=slots
    return smap


if __name__=='__main__':
    if len(sys.argv) > 1:
        AVAILABILITY_CSV = sys.argv[1]
    if len(sys.argv) > 2:
        STUDENT_SCHEDULE_CSV = sys.argv[2]

    availability = read_availability(AVAILABILITY_CSV)
    student_schedule = read_student_schedule(STUDENT_SCHEDULE_CSV)
    schedule=defaultdict(list)
    for s,slots in student_schedule.items():
        for slot in slots:
            schedule[slot].append(s)
    check1_all=True # all students have their MUSTs
    for student,prefs in availability.items():
        for slot,code in prefs.items():
            if code=='MUST':
                assigned=schedule.get(slot,[])
                if student not in assigned: check1_all=False
    check2_all=True # all students doesn't have their CANNOTS
    for student,prefs in availability.items():
        for slot,code in prefs.items():
            if code=='CANNOT':
                assigned=schedule.get(slot,[])
                if student in assigned: check2_all=False
    check3_all=True # each student has 2-3 slots
    for student,slots in student_schedule.items():
           if not (2 <= len(slots) <= 3): check3_all=False
    check4_all=True # each slot has 1-2 students
    for slot,students in schedule.items():
           if not (1 <= len(students) <= 2): check4_all=False
    print('CHECK1:',check1_all)
    print('CHECK2:',check2_all)
    print('CHECK3:',check3_all)
    print('CHECK4:',check4_all)
