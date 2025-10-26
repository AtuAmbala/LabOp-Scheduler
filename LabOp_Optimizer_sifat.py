import csv
import sys
import re
from collections import defaultdict
import pulp

AV_CSV = 'LabOp Timeslot Preference Selection Form - Filled.csv'
OUT_LONG = 'LabOp_Schedule_Long_sifat.csv'
OUT_CAL = 'LabOp_Schedule_sifat.csv'
OUT_STUD = 'LabOp_Student_Schedule_sifat.csv'

LAB_HOURS = [
    ('Monday', 9, 21),('Tuesday', 9, 21),('Wednesday', 9, 21),('Thursday', 9, 21),('Friday', 9, 16),('Saturday', 12, 16),('Sunday', 12, 17)
]

def fmt(h):
    if h==12: return '12 PM'
    if h==24 or h==0: return '12 AM'
    return f"{h if h<=12 else h-12} {'AM' if h<12 else 'PM'}"


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

slots = []
for d,s,e in LAB_HOURS:
    for h in range(s,e):
        slots.append(f"{d} {fmt(h)} - {fmt(h+1)}")
input_csv = sys.argv[1] if len(sys.argv) > 1 else AV_CSV
with open(input_csv, newline='') as f:
    r = csv.reader(f)
    rows = list(r)
hdr = None
start = 1
for i in range(min(5, len(rows))):
    row = rows[i]
    if any((c or '').strip().lower() in ('name', '\ufeffname', 'first name', 'first', 'email', 'last name') for c in row):
        hdr = row; start = i+1; break
if hdr is None:
    hdr = rows[0]; start = 1
header_cols = hdr
mapped_slots = []
slot_indices = []
for i,col in enumerate(header_cols[1:]):
    if col is None:
        mapped_slots.append(None); continue
    key = str(col).strip()
    if key.lower().startswith('slot'):
        slot_indices.append(i)
        mapped_slots.append(None)
    else:
        mapped_slots.append(key)
for k, idx in enumerate(slot_indices):
    if k < len(slots):
        mapped_slots[idx] = slots[k]

students = []
avail = defaultdict(dict)
for row in rows[start:]:
    if not row: continue
    try:
        row_map = {h: (row[i] if i < len(row) else '') for i,h in enumerate(header_cols)}
    except Exception:
        row_map = {}
    name = ''
    if 'First name' in header_cols and 'Last name' in header_cols:
        fn = (row_map.get('First name','') or '').strip()
        ln = (row_map.get('Last name','') or '').strip()
        name = (fn + ' ' + ln).strip()
    if not name and 'Name' in header_cols:
        name = (row_map.get('Name','') or '').strip()
    if not name and 'Email' in header_cols:
        name = (row_map.get('Email','') or '').strip()
    if not name:
        for v in row:
            if v and str(v).strip():
                name = str(v).strip(); break
    if not name: continue
    students.append(name)
    for i,slot in enumerate(mapped_slots):
        v = ''
        try:
            v = row[1+i].strip()
        except:
            v = ''
        val = (v or '').upper()
        if val == 'MUST-SELECT': code = 'MUST'
        elif val == 'CANNOT-SELECT': code = 'CANNOT'
        else: code = 'OK'
        if i < len(slots) and slot:
            avail[name][slot] = code
prob = pulp.LpProblem('lab', pulp.LpMaximize)
assign = {(s,t): pulp.LpVariable(f"x_{i}_{j}", cat='Binary')
          for i,s in enumerate(students) for j,t in enumerate(slots)}

for s in students:
    for t in slots:
        if avail[s].get(t) == 'CANNOT':
            prob += assign[(s,t)] == 0
        if avail[s].get(t) == 'MUST':
            prob += assign[(s,t)] == 1

for t in slots:
    prob += pulp.lpSum(assign[(s,t)] for s in students) >= 1
    prob += pulp.lpSum(assign[(s,t)] for s in students) <= 2

for s in students:
    prob += pulp.lpSum(assign[(s,t)] for t in slots) >= 2
    prob += pulp.lpSum(assign[(s,t)] for t in slots) <= 3

prob += pulp.lpSum(assign.values())

prob.solve(pulp.PULP_CBC_CMD(msg=0))
schedule = defaultdict(list)
student_slots = defaultdict(list)
if pulp.LpStatus[prob.status] != 'Optimal':
    print('not possible')
    raise SystemExit(1)
for s in students:
    for t in slots:
        val = pulp.value(assign[(s,t)])
        if val is not None and val > 0.5:
            schedule[t].append(s)
            student_slots[s].append(t)
with open(OUT_LONG,'w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['Time Slot','Student 1','Student 2'])
    for t in slots:
        s= schedule[t][:2]
        s += ['']*(2-len(s))
        w.writerow([t]+s)
day_order=[d for d,_,_ in LAB_HOURS]
time_map=defaultdict(dict)
for t,ss in schedule.items():
    d,rest=t.split(' ',1)
    time_map[rest][d]='\\n'.join(ss[:2])
def time_key(rest):
    start=rest.split(' - ')[0]
    start=start.replace('12 NOON','12 PM')
    parts=start.split()
    try:
        num=int(parts[0])
    except:
        return 0
    ampm=parts[1] if len(parts)>1 else 'AM'
    if ampm=='AM':
        h=0 if num==12 else num
    else:
        h=12 if num==12 else num+12
    return h
rows=[]
for rest in sorted(time_map.keys(), key=time_key):
    row={'Start Time':rest}
    for d in day_order:
        row[d]=time_map[rest].get(d,'')
    rows.append(row)
with open(OUT_CAL,'w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['Start Time']+day_order)
    for r in rows:
        w.writerow([r['Start Time']]+[r[d] for d in day_order])

maxh=3
with open(OUT_STUD,'w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['Student']+[f'Hour {i+1}' for i in range(maxh)])
    for s in students:
        hours = [normalize_slot(h) for h in student_slots[s]]
        row=[normalize_name(s)]+hours+['']*(maxh-len(hours))
        w.writerow(row)
