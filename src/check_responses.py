import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labop_common import MAX_MUST_HAVE_PER_STUDENT, MUST_HAVE, UNAVAILABLE, get_slot_columns

# Thresholds informed by experimentation/fall-2026's feasibility sweep
# (39 students x 39 slots, exactly 2 slots/student):
#   - unavailable <= 30/student keeps feasibility near 100% as long as the
#     class-wide MUST-HAVE total also stays low; unavailable >= 33 collapses
#     feasibility regardless of MUST-HAVEs.
#   - total MUST-HAVE volume matters more than any single student's count
#     (each student is already hard-capped at 1 MUST-HAVE in practice, 2 at
#     most by the solver): staying <= 15 total keeps most (must_have,
#     unavailable) cells above ~65% feasible; beyond ~25 it's a coin flip or
#     worse. Re-run the sweep if class size or slot count ever changes.
MAX_UNAVAILABLE_PER_STUDENT_WARNING = 30
MAX_TOTAL_MUST_HAVE_WARNING = 15

input_path = sys.argv[1] if len(sys.argv) > 1 else "responses.csv"
df = pd.read_csv(input_path)
pref_cols = get_slot_columns(df)
student_violations = []
slot_violations = []
total_must = 0

for idx, row in df.iterrows():
    must_count = (row[pref_cols] == MUST_HAVE).sum()
    unavailable_count = (row[pref_cols] == UNAVAILABLE).sum()
    total_must += must_count
    if must_count > MAX_MUST_HAVE_PER_STUDENT or unavailable_count > MAX_UNAVAILABLE_PER_STUDENT_WARNING:
        student_violations.append({
            "ID": row["ID"],
            "Name": row["Name"],
            "MUST-HAVE": must_count,
            "UNAVAILABLE": unavailable_count
        })

for slot in pref_cols:
    col = df[slot]
    must_count = (col == MUST_HAVE).sum()
    available_count = (~col.isin([UNAVAILABLE])).sum()
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
if total_must > MAX_TOTAL_MUST_HAVE_WARNING:
    print(
        f"WARNING: total MUST-HAVE count ({total_must}) exceeds the recommended "
        f"class-wide limit of {MAX_TOTAL_MUST_HAVE_WARNING} - feasibility risk climbs "
        f"fast beyond this (see experimentation/fall-2026)."
    )

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
