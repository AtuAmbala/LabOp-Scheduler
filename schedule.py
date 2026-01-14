import sys
import pandas as pd
import pulp as pl
import os

input_path = sys.argv[1]
output_path = sys.argv[2]
input_path = os.path.join(os.getcwd(), input_path)
output_path = os.path.join(os.getcwd(), output_path)

df = pd.read_csv(input_path)

students = df.iloc[:, 3].astype(str).tolist()
slots = df.columns[8:].tolist()

preferences = {
    (s, t): str(df.loc[i, t]).strip().upper()
    for i, s in enumerate(students)
    for t in slots
}

model = pl.LpProblem('slot_assignment', pl.LpMinimize)
assign = pl.LpVariable.dicts(
    'assign',
    [(s, t) for s in students for t in slots],
    0,
    1,
    pl.LpBinary
)

model += 0

for s in students:
    model += pl.lpSum(assign[(s, t)] for t in slots) >= 2
    model += pl.lpSum(assign[(s, t)] for t in slots) <= 3

for t in slots:
    model += pl.lpSum(assign[(s, t)] for s in students) == 2

for s in students:
    for t in slots:
        value = preferences[(s, t)]
        if "MUST-HAVE" in value:
            model += assign[(s, t)] == 1
        if "UNAVAILABLE" in value:
            model += assign[(s, t)] == 0
model.solve()

if pl.LpStatus[model.status] != 'Optimal':
    print('NO OPTIMAL ASSIGNMENT')
else:
    student_info = {}
    for _, row in df.iterrows():
        email = str(row["Email"])
        student_info[email] = (
            row["ID"],
            row["Last name"],
            row["First name"],
        )

    rows_students = []
    for s in students:
        chosen = [t for t in slots if pl.value(assign[(s, t)]) > 0.5]
        chosen = chosen[:3] + [""] * (3 - len(chosen))
        sid, lname, fname = student_info.get(s, ("", "", ""))
        rows_students.append([sid, s, lname, fname] + chosen)

    pd.DataFrame(
        rows_students,
        columns=[
            "student_id",
            "student_email",
            "student_last_name",
            "student_first_name",
            "slot 1",
            "slot 2",
            "slot 3",
        ],
    ).to_csv(output_path.replace(".csv", "_by_students.csv"), index=False)

    rows_slots = []
    for t in slots:
        assigned_students = [s for s in students if pl.value(assign[(s, t)]) > 0.5]
        assigned_students = assigned_students[:2] + [""] * (2 - len(assigned_students))
        rows_slots.append([t] + assigned_students)

    pd.DataFrame(
        rows_slots,
        columns=["slot", "student 1", "student 2"],
    ).to_csv(output_path.replace(".csv", "_by_slot.csv"), index=False)
