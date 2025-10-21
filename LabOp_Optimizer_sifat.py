import csv
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

slots=[]
for d,s,e in LAB_HOURS:
    for h in range(s,e):
        slots.append(f"{d} {fmt(h)} - {fmt(h+1)}")
with open(AV_CSV,newline='') as f:
    r=csv.reader(f)
    rows=list(r)
hdr=None
for i in range(3):
    if any(c.strip().lower().startswith('name') for c in rows[i]):
        hdr=rows[i]; start=i+1; break
if hdr is None: hdr=rows[0]; start=1
cols=hdr[1:]
students=[]
avail=defaultdict(dict)
for row in rows[start:]:
    if not row: continue
    name=row[0].strip()
    if not name: continue
    students.append(name)
    for i,col in enumerate(cols):
        if 1+i<len(row):
            v=row[1+i].strip().upper()
        else:
            v=''
        if v=='MUST-SELECT': code='MUST'
        elif v=='CANNOT-SELECT': code='CANNOT'
        else: code='OK'
        if i<len(slots):
            avail[name][slots[i]]=code
prob = pulp.LpProblem('lab', pulp.LpMaximize)
assign = {(s,t): pulp.LpVariable(f"x_{i}_{j}", cat='Binary')
          for i,s in enumerate(students) for j,t in enumerate(slots)}
for s in students:
    for t in slots:
        if avail[s].get(t)=='CANNOT': prob += assign[(s,t)] == 0
for t in slots:
    prob += pulp.lpSum(assign[(s,t)] for s in students) <= 2
    # lower bound via slack z_t
for s in students:
    prob += pulp.lpSum(assign[(s,t)] for t in slots) <= 3
    # lower bound via slack y_s
y = {s: pulp.LpVariable(f"y_{i}", lowBound=0, cat='Integer') for i,s in enumerate(students)}
z = {t: pulp.LpVariable(f"z_{j}", lowBound=0, cat='Integer') for j,t in enumerate(slots)}
for i,s in enumerate(students):
    prob += pulp.lpSum(assign[(s,t)] for t in slots) + y[s] >= 2
for j,t in enumerate(slots):
    prob += pulp.lpSum(assign[(s,t)] for s in students) + z[t] >= 1
must_terms = [assign[(s,t)] for s in students for t in slots if avail[s].get(t)=='MUST']
PENALTY = 1000000
prob += pulp.lpSum(must_terms) - PENALTY*(pulp.lpSum(y.values()) + pulp.lpSum(z.values())) + 0.01*pulp.lpSum(assign.values())
prob.solve(pulp.PULP_CBC_CMD(msg=0))
schedule = defaultdict(list)
student_slots = defaultdict(list)
if pulp.LpStatus[prob.status] != 'Optimal' and pulp.LpStatus[prob.status] != 'Feasible':
    raise SystemExit(f"Solver status: {pulp.LpStatus[prob.status]}")
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
        row=[s]+student_slots[s]+['']*(maxh-len(student_slots[s]))
        w.writerow(row)
