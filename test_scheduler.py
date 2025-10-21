import csv
from collections import defaultdict

AVAILABILITY_CSV = 'LabOp Timeslot Preference Selection Form - Filled.csv'
STUDENT_SCHEDULE_CSV = 'LabOp_Student_Schedule_sifat.csv'

AVAILABILITY_MAP = {'MUST-SELECT': 'MUST', 'CANNOT-SELECT': 'CANNOT', 'OK': 'OK'}

def read_availability(filepath):
    with open(filepath, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return {}
    header_row = None
    for r in rows[:5]:
        if any(h.strip().lower() in ('name', '\ufeffname', '﻿name') for h in r):
            header_row = r; break
    if header_row is None: header_row = rows[0]
    LAB_HOURS = [('Monday',9,21),('Tuesday',9,21),('Wednesday',9,21),('Thursday',9,21),('Friday',9,16),('Saturday',12,16),('Sunday',12,17)]
    def fmt_label(h):
        if h==12: return '12 PM'
        if h==0 or h==24: return '12 AM'
        if h<12: return f"{h} AM"
        return f"{h-12} PM"
    canonical_slots=[]
    for day,start,end in LAB_HOURS:
        for h in range(start,end): canonical_slots.append(f"{day} {fmt_label(h)} - {fmt_label(h+1)}")
    column_map={}
    day_order=[d for d,_,_ in LAB_HOURS]
    for day_index,day in enumerate(day_order):
        suffix = '' if day_index==0 else str(day_index)
        start_hr,end_hr = LAB_HOURS[day_index][1],LAB_HOURS[day_index][2]
        for hour in range(start_hr,end_hr):
            s_label=fmt_label(hour); e_label=fmt_label(hour+1)
            key1=f"{s_label} - {e_label}{suffix}"; value=f"{day} {s_label} - {e_label}"; column_map[key1]=value
            if s_label=='12 PM': column_map[f"12 NOON - {e_label}{suffix}"]=value
            if e_label=='12 PM': column_map[f"{s_label} - 12 NOON{suffix}"]=value
    column_map['Saturday 12 NOON - 1 PM5']='Saturday 12 PM - 1 PM'
    column_map['1 PM - 2 PM5']='Saturday 1 PM - 2 PM'
    column_map['2 PM - 3 PM5']='Saturday 2 PM - 3 PM'
    column_map['3 PM - 4 PM5']='Saturday 3 PM - 4 PM'
    column_map['Sunday 12 NOON - 1 PM6']='Sunday 12 PM - 1 PM'
    column_map['1 PM - 2 PM6']='Sunday 1 PM - 2 PM'
    column_map['2 PM - 3 PM6']='Sunday 2 PM - 3 PM'
    column_map['3 PM - 4 PM6']='Sunday 3 PM - 4 PM'
    column_map['4 PM - 5 PM6']='Sunday 4 PM - 5 PM'
    header_cols=header_row
    mapped_slots=[]
    for col in header_cols[1:]:
        if col is None: mapped_slots.append(None); continue
        key=col.strip()
        if key in column_map: mapped_slots.append(column_map[key]); continue
        stripped=key.rstrip('0123456789').strip()
        if stripped in column_map: mapped_slots.append(column_map[stripped]); continue
        parts=key.split(' ',1)
        if parts[0] in day_order and len(parts)>1: mapped_slots.append(key); continue
        mapped_slots.append(None)
    student_map={}
    start_idx = rows.index(header_row)+1
    for row in rows[start_idx:]:
        if not row: continue
        name=row[0].strip()
        if not name: continue
        availability={}
        for i,slot in enumerate(mapped_slots):
            val=''
            try: val=row[1+i].strip()
            except: val=''
            code=AVAILABILITY_MAP.get(val.upper(),'OK') if val else 'OK'
            if slot: availability[slot]=code
        student_map[name]=availability
    return student_map


def read_student_schedule(filepath):
    smap={}
    with open(filepath, newline='') as f:
        reader=csv.DictReader(f)
        for r in reader:
            student=(r.get('Student') or '').strip()
            if not student: continue
            slots=[]
            for k in list(r.keys()):
                if k and k.startswith('Hour'):
                    v=(r.get(k) or '').strip()
                    if v: slots.append(v)
            smap[student]=slots
    return smap


if __name__=='__main__':
    availability=read_availability(AVAILABILITY_CSV)
    student_schedule=read_student_schedule(STUDENT_SCHEDULE_CSV)
    schedule=defaultdict(list)
    for s,slots in student_schedule.items():
        for slot in slots:
            schedule[slot].append(s)
    check1_all=True
    for student,prefs in availability.items():
        for slot,code in prefs.items():
            if code=='MUST':
                assigned=schedule.get(slot,[])
                if student not in assigned: check1_all=False
    check2_all=True
    for student,prefs in availability.items():
        for slot,code in prefs.items():
            if code=='CANNOT':
                assigned=schedule.get(slot,[])
                if student in assigned: check2_all=False
    check3_all=True
    for student,slots in student_schedule.items():
        if len(slots)!=3: check3_all=False
    check4_all=True
    for slot,students in schedule.items():
        if len(students)!=2: check4_all=False
    print('CHECK1:',check1_all)
    print('CHECK2:',check2_all)
    print('CHECK3:',check3_all)
    print('CHECK4:',check4_all)
