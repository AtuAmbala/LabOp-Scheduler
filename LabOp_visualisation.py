import sys
import pandas as pd
import os
from collections import defaultdict
from typing import List, Dict, Tuple, Any

# --- Time Slot Definitions for Calendar Formatting ---

# Define the full lab hours to generate chronological, clean time slot names
LAB_HOURS = {
    'Monday': (9, 21),      # 9 AM to 9 PM (9-10 to 8-9)
    'Tuesday': (9, 21),
    'Wednesday': (9, 21),
    'Thursday': (9, 21),
    'Friday': (9, 16),      # 9 AM to 4 PM
    'Saturday': (12, 16),   # 12 PM to 4 PM
    'Sunday': (12, 17)      # 12 PM to 5 PM
}

# The maximum number of slots a student can be assigned (from your initial problem constraints)
MAX_SLOTS_PER_STUDENT = 3 

def _format_time(hour: int) -> str:
    """Formats a single hour integer (0-23) to a human-readable 12-hour string."""
    if hour == 12:
        return '12 PM'
    if hour == 24 or hour == 0:
        return '12 AM'
    dt = pd.to_datetime(f'{hour}:00', format='%H:%M')
    return dt.strftime('%I %p').lstrip('0')

def generate_full_time_slots() -> List[str]:
    """Generates a list of all 1-hour time slot strings in chronological order."""
    slots = []
    for day, (start_hr, end_hr) in LAB_HOURS.items():
        for hour in range(start_hr, end_hr):
            start_time = _format_time(hour)
            end_time = _format_time(hour + 1)
            slot_name = f"{day} {start_time} - {end_time}"
            slots.append(slot_name)
    return slots

# --- Export Function 1: Calendar Timetable (Wide Format with Newlines) ---

def export_calendar_schedule(schedule_dict: Dict[str, List[str]], export_path: str):
    """
    Converts the schedule dictionary into the wide (calendar) format and exports to CSV.
    Students in the same slot are separated by a newline character (\n).
    """
    # 1. Prepare data for wide format (Day columns, Time rows)
    calendar_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(str))
    
    # Split "Day Time - Time" into Day and Time
    for full_slot, students in schedule_dict.items():
        if not students: continue
            
        parts = full_slot.split(' ', 1)
        day = parts[0]
        time_slot = parts[1]
        
        # Combine student names into a single string, separated by newlines (\n)
        calendar_data[time_slot][day] = '\n'.join(students)
        
    # 2. Structure DataFrame
    def sort_key(time_str):
        start_time_str = time_str.split(' - ')[0]
        try:
            return pd.to_datetime(start_time_str, format='%I %p').time()
        except ValueError:
            return start_time_str 
            
    time_slots = sorted(calendar_data.keys(), key=sort_key)
    day_order = list(LAB_HOURS.keys())
    
    calendar_records = []
    for time_slot in time_slots:
        record = {'Time Slot': time_slot} 
        for day in day_order:
            record[day] = calendar_data.get(time_slot, {}).get(day, '')
        calendar_records.append(record)
        
    calendar_df = pd.DataFrame(calendar_records)
    calendar_df = calendar_df[['Time Slot'] + day_order]
    
    # 3. Export to CSV
    calendar_df.to_csv(export_path, index=False)
    print(f"\n✅ --- Exported Calendar Timetable View to {export_path} ---")

# --- Export Function 2: Student Slot List (Side-by-Side Hours) ---

def export_student_slot_list(schedule_dict: Dict[str, List[str]], filepath: str, max_hours: int):
    """
    Exports the schedule as a list of hours assigned to each student in chronological order.
    Format: Student, Slot 1, Slot 2, Slot 3
    """
    student_hours_map = defaultdict(list)
    
    # Get all full slot names in chronological order (for sorting later)
    chronological_slots = generate_full_time_slots()
    
    # Populate map: Student -> [Slot 1, Slot 2, ...] in chronological order
    for full_slot in chronological_slots:
        # Check if this slot was assigned to anyone
        students = schedule_dict.get(full_slot, [])
        for student in students:
            if student: 
                student_hours_map[student].append(full_slot)
    
    # Build DataFrame records
    records = []
    hour_columns = [f'Slot {i+1}' for i in range(max_hours)]
    
    for student, slots in student_hours_map.items():
        record = {'Student': student}
        
        # Fill in assigned hours (up to max_hours)
        for i, slot in enumerate(slots):
            if i < max_hours: 
                record[hour_columns[i]] = slot
            
        # Fill remaining hour columns with empty string
        for i in range(len(slots), max_hours):
            record[hour_columns[i]] = ''
            
        records.append(record)

    student_summary_df = pd.DataFrame(records)
    
    # Ensure proper column order
    required_cols = ['Student'] + hour_columns
    student_summary_df = student_summary_df.reindex(columns=required_cols, fill_value='')

    # Export
    student_summary_df.to_csv(filepath, index=False)
    print(f"✅ --- Exported Student Slot List to {filepath} ---")
    
# --- Export Function 3: Slot-Centric Flat Schedule ---

def export_slot_centric_schedule(schedule_dict: Dict[str, List[str]], export_path: str):
    """
    Exports the schedule as a slot-centric wide list: Time Slot, Student 1, Student 2, ...
    This creates one row per time slot with students listed side-by-side.
    """
    wide_list_data = []
    
    # Get all full slot names in chronological order
    full_slots_in_order = generate_full_time_slots()
    
    # Determine the maximum number of students assigned to any single slot
    max_students_per_slot = max(len(students) for students in schedule_dict.values()) if schedule_dict else 0
    
    # Create the column headers dynamically (e.g., 'Student 1', 'Student 2')
    student_columns = [f'Student {i+1}' for i in range(max_students_per_slot)]
    
    # Iterate through all possible slots chronologically
    for full_slot in full_slots_in_order:
        students = schedule_dict.get(full_slot, [])
        record = {'Time Slot': full_slot}
        
        # Fill in assigned students side-by-side
        for i, student in enumerate(students):
            record[student_columns[i]] = student
        
        # Fill remaining student columns with empty strings
        for i in range(len(students), max_students_per_slot):
            if i < len(student_columns): # Safety check
                record[student_columns[i]] = ''
        
        # Only add slots that were actually used to keep the output clean
        if students:
            wide_list_data.append(record)
            
    # Create DataFrame
    required_cols = ['Time Slot'] + student_columns
    wide_list_df = pd.DataFrame(wide_list_data)
    wide_list_df = wide_list_df.reindex(columns=required_cols, fill_value='')
    
    # Export
    wide_list_df.to_csv(export_path, index=False)
    print(f"✅ --- Exported Slot-Centric Wide List to {export_path} ---")
    
# --- Main Script Execution ---

if __name__ == '__main__':
    # 🛑 Check for command line arguments
    if len(sys.argv) < 2:
        print("Usage: python LabOp_visualisation.py <input_assignment_csv_path>")
        sys.exit(1)

    input_file_path = sys.argv[1] 
    
    # Define output paths
    timetable_output_path = 'LabOp_timetable_output.csv' 
    long_schedule_output_path = 'LabOp_student_slot_list_output.csv' # Renamed for clarity
    flat_schedule_output_path = 'LabOp_flat_schedule_output.csv'
    # --- Load Data ---
    try:
        input_df = pd.read_csv(input_file_path)
        print(f"Successfully loaded input file: **{input_file_path}**")
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the CSV: {e}")
        sys.exit(1)

    # --- Data Preparation (Mapping Simple Slot IDs to Full Names) ---
    
    all_full_slots = generate_full_time_slots() 
    
    # ASSUMPTION: 'Slot 1' corresponds to all_full_slots[0], 'Slot 2' to all_full_slots[1], etc.
    slot_ids = [f'Slot {i+1}' for i in range(len(all_full_slots))]
    slot_id_to_full_name = {}
    
    try:
        slot_id_to_full_name = {slot_ids[i]: all_full_slots[i] for i in range(len(all_full_slots))}
    except IndexError:
        print("ERROR: Slot list length mismatch. Cannot map simple slot IDs to full time names.")
        sys.exit(1)

    # Dictionary to build the calendar schedule: {Full Slot Name: [Student 1, Student 2]}
    schedule_dict_for_calendar = defaultdict(list)
    
    # --- Processing Assignment Data ---

    student_col_name = input_df.columns[0]
    slot_cols = [col for col in input_df.columns if 'slot' in col.lower() and col != student_col_name]

    if not slot_cols:
        print("Error: Could not find assignment columns (e.g., 'slot 1', 'slot 2'). Check your CSV column headers.")
        sys.exit(1)

    for index, row in input_df.iterrows():
        student_id = str(row[student_col_name])
        
        for col in slot_cols:
            simple_slot_id = str(row[col]).strip()
            
            if simple_slot_id and simple_slot_id.lower().startswith('slot'):
                
                full_slot_name = slot_id_to_full_name.get(simple_slot_id)
                
                if full_slot_name:
                    schedule_dict_for_calendar[full_slot_name].append(student_id)
                # else: (Warning handled in the previous exchange)

    # --- Export Outputs ---
    
    print("\n--- Starting Schedule Generation ---")

    # 1. Export the Calendar Timetable
    export_calendar_schedule(schedule_dict_for_calendar, timetable_output_path)
    
    # 2. Export the Student Slot List (Side-by-Side Hours)
    export_student_slot_list(schedule_dict_for_calendar, long_schedule_output_path, MAX_SLOTS_PER_STUDENT)

    # 3. Export the Slot-Centric Schedule
    export_slot_centric_schedule(schedule_dict_for_calendar, flat_schedule_output_path)

    print("--- Schedule Generation Complete ---")