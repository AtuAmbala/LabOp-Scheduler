import csv
import sys
import re
from collections import defaultdict

AVAILABILITY_CSV = 'LabOp Timeslot Preference Selection Form - Filled.csv'
STUDENT_SCHEDULE_CSV = 'LabOp_Student_Schedule.csv'

AVAILABILITY_MAP = {'MUST-SELECT': 'MUST', 'CANNOT-SELECT': 'CANNOT', 'OK': 'OK'}

LAB_HOURS = [('Monday',9,21),('Tuesday',9,21),('Wednesday',9,21),('Thursday',9,21),('Friday',9,16),('Saturday',12,16),('Sunday',12,17)]

def fmt_label(h):
    if h==12: return '12 PM'
    if h==0 or h==24: return '12 AM'
    if h<12: return f"{h} AM"
    return f"{h-12} PM"

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

def canonical_slots_list():
    out=[]
    for day,start,end in LAB_HOURS:
        for h in range(start,end):
            out.append(f"{day} {fmt_label(h)} - {fmt_label(h+1)}")
    return out

CANONICAL_SLOTS_RAW = canonical_slots_list()
CANONICAL_SLOTS = set(normalize_slot(x) for x in CANONICAL_SLOTS_RAW)

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
    header_cols = header_row
    mapped_slots = []
    slot_cols = []
    for col in header_cols[1:]:
        if col is None:
            mapped_slots.append(None)
            continue
        key = str(col).strip()
        if key.lower().startswith('slot'):
            slot_cols.append(key)
            mapped_slots.append(None)
            continue
        mapped_slots.append(key)
    if slot_cols:
        indices = [i for i,c in enumerate(header_cols[1:]) if c and str(c).strip().lower().startswith('slot')]
        k = 0
        for idx in indices:
            if k < len(CANONICAL_SLOTS_RAW):
                mapped_slots[idx] = CANONICAL_SLOTS_RAW[k]
                k += 1
    start_idx = rows.index(header_row) + 1
    student_map = {}
    for row in rows[start_idx:]:
        if not row:
            continue
        try:
            row_map = {h: (row[i] if i < len(row) else '') for i,h in enumerate(header_cols)}
        except Exception:
            row_map = {}
        name = ''
        if 'First name' in header_cols and 'Last name' in header_cols:
            try:
                fn = (row_map.get('First name','') or '').strip()
                ln = (row_map.get('Last name','') or '').strip()
                name = (fn + ' ' + ln).strip()
            except:
                name = ''
        if not name and 'Name' in header_cols:
            name = (row_map.get('Name','') or '').strip()
        if not name and 'Email' in header_cols:
            name = (row_map.get('Email','') or '').strip()
        if not name:
            for v in row:
                if v and str(v).strip():
                    name = str(v).strip(); break
        if not name:
            continue
        name_key = normalize_name(name)
        availability = {}
        for i,slot in enumerate(mapped_slots):
            val = ''
            try:
                val = (row[1+i] or '').strip()
            except:
                val = ''
            if not slot:
                continue
            ns = normalize_slot(slot)
            if ns not in CANONICAL_SLOTS:
                continue
            code = AVAILABILITY_MAP.get(val.upper(),'OK') if val else 'OK'
            availability[ns] = code
        student_map[name_key] = availability
    return student_map

def read_student_schedule(filepath):
    smap={}
    with open(filepath, newline='') as f:
        reader=csv.DictReader(f)
        for r in reader:
            student=(r.get('Student') or '').strip()
            if not student:
                continue
            student_key = normalize_name(student)
            slots=[]
            for k in list(r.keys()):
                if k and k.startswith('Hour'):
                    v=(r.get(k) or '').strip()
                    if v:
                        sv = normalize_slot(v)
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
            if slot in CANONICAL_SLOTS:
                schedule[slot].append(s)

    schedule_unique = {slot: list(dict.fromkeys(students)) for slot, students in schedule.items()}
    student_unique_slots = {s: list(dict.fromkeys([sl for sl in slots if sl in CANONICAL_SLOTS])) for s, slots in student_schedule.items()}

    check1_all=True
    missing_must=[]
    for student,prefs in availability.items():
        for slot,code in prefs.items():
            if code=='MUST':
                assigned=schedule_unique.get(slot,[])
                if student not in assigned:
                    check1_all=False
                    missing_must.append((student,slot))

    check2_all=True
    has_cannot=[]
    for student,prefs in availability.items():
        for slot,code in prefs.items():
            if code=='CANNOT':
                assigned=schedule_unique.get(slot,[])
                if student in assigned:
                    check2_all=False
                    has_cannot.append((student,slot))

    check3_all=True
    bad_student_hours=[]
    for student,slots in student_unique_slots.items():
        if not (2 <= len(slots) <= 3):
            check3_all=False
            bad_student_hours.append((student,len(slots)))

    check4_all=True
    bad_slots=[]
    for slot in CANONICAL_SLOTS:
        students_here = schedule_unique.get(slot, [])
        if not (1 <= len(students_here) <= 2):
            check4_all=False
            bad_slots.append((slot,len(students_here)))

    no_dupes_per_slot = all(len(v) == len(dict.fromkeys(v)) for v in schedule.values())
    unknown_slots_ok = all(slot in CANONICAL_SLOTS for slot in schedule.keys())
    all_students_av = set(availability.keys())
    all_students_sched = set(student_unique_slots.keys())
    unknown_students_ok = all(s in all_students_av for s in all_students_sched)
    all_availability_students_present = all(s in all_students_sched for s in all_students_av)

    print('CHECK1_ALL_MUST_SATISFIED:',check1_all)
    print('CHECK2_ALL_CANNOT_RESPECTED:',check2_all)
    print('CHECK3_STUDENT_2_TO_3_HOURS:',check3_all)
    print('CHECK4_EACH_SLOT_1_TO_2_STAFFED:',check4_all)
    print('CHECK5_NO_DUPES_PER_SLOT_LIST:',no_dupes_per_slot)
    print('CHECK6_NO_UNKNOWN_SLOTS_IN_SCHEDULE:',unknown_slots_ok)
    print('CHECK7_NO_UNKNOWN_STUDENTS_IN_SCHEDULE:',unknown_students_ok)
    print('CHECK8_ALL_AVAILABILITY_STUDENTS_PRESENT_IN_SCHEDULE:',all_availability_students_present)

    if not check1_all and missing_must:
        print('MISSING_MUST:', missing_must)
    if not check2_all and has_cannot:
        print('HAS_CANNOT_VIOLATIONS:', has_cannot)
    if not check3_all and bad_student_hours:
        print('BAD_STUDENT_HOUR_COUNTS:', bad_student_hours)
    if not check4_all and bad_slots:
        print('BAD_SLOT_STAFFING:', bad_slots)
