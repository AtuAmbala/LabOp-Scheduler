import sys
import pandas as pd
import os
import math

def clean_slot_list(values):
    result = []
    if len(values) == 1 and isinstance(values[0], str) and ',' in values[0]:
        values = values[0].split(',')
        
    for v in values:
        if isinstance(v, str) and v.strip() != "":
            result.append(v.strip())
        elif not isinstance(v, str) and not (v is None or (isinstance(v, float) and math.isnan(v))):
            result.append(str(v).strip())
    return result

def main():
    if len(sys.argv) != 4:
        print("Usage: python check_output.py <responses.csv> <schedule_by_student.csv> <schedule_by_slot.csv>")
        sys.exit(1)
        
    prefs_path = os.path.join(os.getcwd(), sys.argv[1])
    student_sched_path = os.path.join(os.getcwd(), sys.argv[2])
    slot_sched_path = os.path.join(os.getcwd(), sys.argv[3])
    
    prefs_df = pd.read_csv(prefs_path)
    student_df = pd.read_csv(student_sched_path)
    slot_df = pd.read_csv(slot_sched_path)
    
    slot_columns = prefs_df.columns[8:].tolist()
    
    prefs_by_email = {}
    for _, row in prefs_df.iterrows():
        email = str(row["Email"]).strip()
        prefs_by_email[email] = row
    
    student_slot_uniq_violations = []
    must_have_violations = []
    unavailable_violations = []
    student_slot_count_violations = [] 
    
    for i, row in student_df.iterrows():
        email = str(row["Student"]).strip()
        assigned_slots = clean_slot_list([row["Assigned Slots"]])
        
        if len(assigned_slots) != len(set(assigned_slots)):
            student_slot_uniq_violations.append(email)
            
        if not (2 <= len(assigned_slots) <= 3):
            student_slot_count_violations.append((email, len(assigned_slots)))
            
        if email not in prefs_by_email:
            continue
            
        prefs_row = prefs_by_email[email]
        
        for slot in slot_columns:
            value = prefs_row[slot]
            if isinstance(value, float) and math.isnan(value):
                pref = ""
            else:
                pref = str(value).strip().upper()
                
            if "MUST-HAVE" in pref and slot not in assigned_slots:
                must_have_violations.append((email, slot))
                
            if "UNAVAILABLE" in pref and slot in assigned_slots:
                unavailable_violations.append((email, slot))
                
    slot_unique_student_violations = []
    slot_student_count_violations = [] 
    
    for _, row in slot_df.iterrows():
        slot_name = str(row["Time Slot"]).strip()
        students_in_slot = clean_slot_list([row["Assigned Students"]])
        
        if len(students_in_slot) != len(set(students_in_slot)):
            slot_unique_student_violations.append(slot_name)

        if len(students_in_slot) != 2:
            slot_student_count_violations.append((slot_name, len(students_in_slot)))

    print("Student schedule checks")
    
    if student_slot_uniq_violations:
        print("Students with non-unique slots:")
        for e in student_slot_uniq_violations:
            print(" ", e)
    else:
        print("All students have unique slots.")
        
    if student_slot_count_violations:
        print("Students with incorrect number of slots (must be 2 or 3):")
        for e, count in student_slot_count_violations:
            print(f"  {e}: {count} assigned")
    else:
        print("All students have 2 or 3 assigned slots.")

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
    
    if slot_student_count_violations:
        print("Slots with incorrect number of students (must be 2):")
        for s, count in slot_student_count_violations:
            print(f"  {s}: {count} assigned")
    else:
        print("All slots have exactly 2 students.")

    if slot_unique_student_violations:
        print("Slots with non-unique students:")
        for s in slot_unique_student_violations:
            print(" ", s)
    else:
        print("All slots have unique students.")

if __name__ == "__main__":
    main()