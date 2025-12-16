import pandas as pd

df = pd.read_csv("responses.csv")
pref_cols = df.columns[8:]
student_violations = []
slot_violations = []
total_must = 0

for idx, row in df.iterrows():
    must_count = (row[pref_cols] == "MUST-HAVE").sum()
    unavailable_count = (row[pref_cols] == "UNAVAILABLE").sum()
    total_must += must_count
    if must_count > 3 or unavailable_count > 20:
        student_violations.append({
            "ID": row["ID"],
            "Name": row["Name"],
            "MUST-HAVE": must_count,
            "UNAVAILABLE": unavailable_count
        })

for slot in pref_cols:
    col = df[slot]
    must_count = (col == "MUST-HAVE").sum()
    available_count = (~col.isin(["UNAVAILABLE"])).sum()
    if must_count > 2:
        slot_violations.append({
            "Slot": slot,
            "Violation": "More than 2 MUST-HAVEs",
            "MUST-HAVE count": must_count
        })
    if available_count < 2:
        slot_violations.append({
            "Slot": slot,
            "Violation": "Less than 2 AVAILABLE students",
            "Available count": available_count
        })

print("Total MUST-HAVE count:", total_must)

if student_violations:
    print("\nStudent-level violations:")
    for v in student_violations:
        print(v)
else:
    print("\nNo student-level violations.")

if slot_violations:
    print("\nSlot-level violations:")
    for v in slot_violations:
        print(v)
else:
    print("\nNo slot-level violations.")
