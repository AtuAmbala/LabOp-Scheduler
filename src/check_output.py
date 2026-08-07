## python check_output.py responses.csv schedule_by_student.csv schedule_by_slot.csv
import sys
import pandas as pd
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labop_common import MUST_HAVE, SLOTS_PER_STUDENT, STUDENTS_PER_SLOT, UNAVAILABLE, get_slot_columns

def clean_slot_list(values):
    result = []
    for v in values:
        if isinstance(v, str) and v.strip() != "":
            result.append(v.strip())
        elif not isinstance(v, str) and not (v is None or (isinstance(v, float) and math.isnan(v))):
            result.append(str(v).strip())
    return result

def main():
    prefs_path = os.path.join(os.getcwd(), sys.argv[1])
    student_sched_path = os.path.join(os.getcwd(), sys.argv[2])
    slot_sched_path = os.path.join(os.getcwd(), sys.argv[3])
    prefs_df = pd.read_csv(prefs_path)
    student_df = pd.read_csv(student_sched_path)
    slot_df = pd.read_csv(slot_sched_path)
    slot_columns = get_slot_columns(prefs_df)
    prefs_by_email = {}
    for _, row in prefs_df.iterrows():
        email = str(row["Email"]).strip()
        prefs_by_email[email] = row
    student_slot_uniq_violations = []
    must_have_violations = []
    unavailable_violations = []
    student_slot_cols = [f"slot {i + 1}" for i in range(SLOTS_PER_STUDENT)]
    for i, row in student_df.iterrows():
        email = str(row["student_email"]).strip()
        assigned_slots = clean_slot_list([row[c] for c in student_slot_cols])
        if len(assigned_slots) != len(set(assigned_slots)):
            student_slot_uniq_violations.append(email)
        if email not in prefs_by_email:
            continue
        prefs_row = prefs_by_email[email]
        for slot in slot_columns:
            value = prefs_row[slot]
            if isinstance(value, float) and math.isnan(value):
                pref = ""
            else:
                pref = str(value).strip().upper()
            if MUST_HAVE in pref and slot not in assigned_slots:
                must_have_violations.append((email, slot))
            if UNAVAILABLE in pref and slot in assigned_slots:
                unavailable_violations.append((email, slot))
    slot_student_cols = [f"student {i + 1}" for i in range(STUDENTS_PER_SLOT)]
    slot_unique_student_violations = []
    for _, row in slot_df.iterrows():
        slot_name = str(row["slot"]).strip()
        students_in_slot = clean_slot_list([row[c] for c in slot_student_cols])
        if len(students_in_slot) != len(set(students_in_slot)):
            slot_unique_student_violations.append(slot_name)
    print("Student schedule checks")
    if student_slot_uniq_violations:
        print("Students with non-unique slots:")
        for e in student_slot_uniq_violations:
            print(" ", e)
    else:
        print("All students have unique slots.")
    if must_have_violations:
        print("MUST-HAVE violations (student_email, slot):")
        for e, slot in must_have_violations:
            print(" ", e, slot)
    else:
        print("All MUST-HAVE constraints satisfied.")
    if unavailable_violations:
        print("UNAVAILABLE violations (student_email, slot):")
        for e, slot in unavailable_violations:
            print(" ", e, slot)
    else:
        print("All UNAVAILABLE constraints satisfied.")
    print("\nSlot schedule checks")
    if slot_unique_student_violations:
        print("Slots with non-unique students:")
        for s in slot_unique_student_violations:
            print(" ", s)
    else:
        print("All slots have unique students.")

if __name__ == "__main__":
    main()
