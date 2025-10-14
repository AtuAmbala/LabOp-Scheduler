import pandas as pd
from collections import defaultdict
import random
from typing import List, Dict, Tuple, Any

# --- Configuration Variables ---

# The number of students required to staff each 1-hour lab session.
SLOTS_PER_HOUR = 2

# The maximum number of hours a student should be assigned for the week.
MAX_HOURS_PER_STUDENT = 2

# --- Time Slot Definitions ---

LAB_HOURS = {
    'Monday': (9, 21),    # 9 AM to 9 PM (exclusive end, so 9-10 to 8-9)
    'Tuesday': (9, 21),
    'Wednesday': (9, 21),
    'Thursday': (9, 21),
    'Friday': (9, 16),    # 9 AM to 4 PM
    'Saturday': (12, 16), # 12 PM to 4 PM
    'Sunday': (12, 17)    # 12 PM to 5 PM
}

# Corrected mapping of the input strings to a simplified availability code
AVAILABILITY_MAP = {
    'MUST-SELECT': 'MUST',
    'CANNOT-SELECT': 'CANNOT',
    'OK': 'OK',
}

def _format_time(hour: int) -> str:
    """Formats a single hour integer (0-23) to a human-readable 12-hour string (e.g., '9 AM', '12 PM')."""
    if hour == 12:
        return '12 PM'
    if hour == 24: 
        return '12 AM'
    dt = pd.to_datetime(f'{hour}:00', format='%H:%M')
    return dt.strftime('%I %p').lstrip('0')

def generate_time_slots() -> List[str]:
    """Generates a list of all 1-hour time slot strings for the week (e.g., 'Monday 9 AM - 10 AM')."""
    slots = []
    for day, (start_hr, end_hr) in LAB_HOURS.items():
        for hour in range(start_hr, end_hr):
            # Use the consistent time formatter
            start_time = _format_time(hour)
            end_time = _format_time(hour + 1)
            slot_name = f"{day} {start_time} - {end_time}"
            slots.append(slot_name)
    return slots

def _generate_csv_column_map() -> Dict[str, str]:
    """
    Generates a map to translate messy CSV column headers (e.g., '9 AM - 10 AM1', '12 NOON - 1 PM2')
    to clean internal slot names (e.g., 'Tuesday 9 AM - 10 AM').
    """
    column_map = {}
    
    # Get ordered list of days
    day_order = list(LAB_HOURS.keys())

    for day_index, day in enumerate(day_order):
        # Monday (index 0) has no suffix. Subsequent days use index+1 as suffix.
        suffix = '' if day_index == 0 else str(day_index)
        
        start_hr, end_hr = LAB_HOURS[day]
        for hour in range(start_hr, end_hr):
            # 1. Generate the clean internal name
            clean_start_time = _format_time(hour)
            clean_end_time = _format_time(hour + 1)
            clean_time_part = f"{clean_start_time} - {clean_end_time}"
            clean_name = f"{day} {clean_time_part}"
            
            # 2. Generate the CSV header based on the specific hour pattern

            csv_header = ""
            
            # Special handling for 11 AM - 12 NOON and 12 NOON - 1 PM slots, applied to all days
            if day in day_order:
                if hour == 11: # 11 AM - 12 PM slot (Mon-Fri)
                    csv_header = f"11 AM - 12 NOON{suffix}"
                elif hour == 12: # 12 PM - 1 PM slot (All days that start or continue past noon)
                    csv_header = f"12 NOON - 1 PM{suffix}"
            
            # If not a special case, use standard formatting
            if not csv_header:
                # Use standard formatting for all other hours in the CSV header
                csv_start_time = pd.to_datetime(f'{hour}:00', format='%H:%M').strftime('%I %p').lstrip('0')
                csv_end_time = pd.to_datetime(f'{hour + 1}:00', format='%H:%M').strftime('%I %p').lstrip('0')
                csv_header = f"{csv_start_time} - {csv_end_time}{suffix}"
            
            # Map the CSV header to the clean internal name
            column_map[csv_header] = clean_name
            
    # Manually fix the Saturday/Sunday columns (where the day name was included in the header)
    # This addresses the manual suffixes we identified in earlier steps.
    column_map['Saturday 12 NOON - 1 PM5'] = 'Saturday 12 PM - 1 PM'
    column_map['1 PM - 2 PM5'] = 'Saturday 1 PM - 2 PM'
    column_map['2 PM - 3 PM5'] = 'Saturday 2 PM - 3 PM'
    column_map['3 PM - 4 PM5'] = 'Saturday 3 PM - 4 PM'

    column_map['Sunday 12 NOON - 1 PM6'] = 'Sunday 12 PM - 1 PM'
    column_map['1 PM - 2 PM6'] = 'Sunday 1 PM - 2 PM'
    column_map['2 PM - 3 PM6'] = 'Sunday 2 PM - 3 PM'
    column_map['3 PM - 4 PM6'] = 'Sunday 3 PM - 4 PM'
    column_map['4 PM - 5 PM6'] = 'Sunday 4 PM - 5 PM'
    
    return column_map

def load_data(filepath: str) -> Tuple[pd.DataFrame, List[str]]:
    """Loads availability data and cleans up student names and availability codes."""
    try:
        # Read the CSV, potentially skipping initial junk rows if necessary
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Error: Input file not found at {filepath}")
        return None, []
    
    # 1. Normalize Column Names
    csv_map = _generate_csv_column_map()
    # Apply mapping only to columns that exist in the DataFrame
    valid_map = {k: v for k, v in csv_map.items() if k in df.columns}
    df.rename(columns=valid_map, inplace=True)

    # 2. Identify Student Column and Time Slot Columns
    if 'Name' not in df.columns:
        # Fallback if 'Name' isn't found, use the first column and warn the user
        df.rename(columns={df.columns[0]: 'Student'}, inplace=True)
        print("Warning: 'Name' column not found. Using the first column as 'Student' identifier.")
    else:
         df.rename(columns={'Name': 'Student'}, inplace=True)

    # List of all valid time slots
    all_clean_slots = generate_time_slots()
    
    # Filter columns: keep 'Student' and only the clean time slot columns
    kept_columns = ['Student'] + [col for col in all_clean_slots if col in df.columns]
    availability_df = df[kept_columns]
    
    # Drop rows where 'Student' is missing
    availability_df.dropna(subset=['Student'], inplace=True)
    
    # 3. Clean up the availability codes in the DataFrame
    # Note: df.columns[1:] now refers to the clean time slot names
    availability_df.iloc[:, 1:] = availability_df.iloc[:, 1:].applymap(
        lambda x: AVAILABILITY_MAP.get(str(x).upper().strip(), 'OK')
    )

    print(f"Loaded {len(availability_df)} students and {len(kept_columns) - 1} relevant time slots.")
    return availability_df, all_clean_slots

def create_schedule(availability_df: pd.DataFrame, slot_names: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, List[str]]]:
    """
    Creates the schedule based on availability, prioritizing MUST assignments and then
    prioritizing filling at least one student in every slot before doubling up.
    """
    
    # Initialize tracking variables
    schedule = {slot: [] for slot in slot_names}
    student_hours = defaultdict(int)
    students = availability_df['Student'].tolist()
    
    # Convert DataFrame to a dictionary for faster lookup: Student -> {Slot: Availability}
    availability_data = availability_df.set_index('Student').T.to_dict()

    # --- PHASE 1: Process MUST assignments (Highest Priority) ---
    print("\nPhase 1: Assigning 'MUST' slots...")
    
    for student in students:
        if student not in availability_data: continue

        # Find all MUST slots for this student
        must_slots = [
            slot for slot, status in availability_data[student].items() 
            if status == 'MUST' and slot in slot_names
        ]
        
        random.shuffle(must_slots)

        for slot in must_slots:
            is_slot_full = len(schedule[slot]) >= SLOTS_PER_HOUR
            is_student_full = student_hours[student] >= MAX_HOURS_PER_STUDENT

            if not is_slot_full and not is_student_full:
                schedule[slot].append(student)
                student_hours[student] += 1
                availability_data[student][slot] = 'ASSIGNED'
                print(f"  --> ASSIGNED MUST: {student} in {slot}. Total hours: {student_hours[student]}")


    # --- PHASE 2A: Coverage Priority (Fill all slots with at least one student using 'OK') ---
    print("\nPhase 2A: Filling empty slots (Coverage Priority) with 'OK'...")
    
    # Sort slots to ensure consistent assignment across runs
    slots_to_fill_coverage = sorted([slot for slot in slot_names if len(schedule[slot]) == 0])

    for slot in slots_to_fill_coverage:
        # We only need 1 student for coverage in this phase
        needed = 1 - len(schedule[slot]) 
        
        if needed > 0:
            # Find eligible students for this slot
            eligible_students = []
            for student in students:
                is_available_ok = availability_data[student].get(slot) == 'OK'
                is_student_full = student_hours[student] >= MAX_HOURS_PER_STUDENT

                if is_available_ok and not is_student_full:
                    # Priority Score: fewest assigned hours
                    priority_score = student_hours[student]
                    eligible_students.append((priority_score, student))

            # Assign the single best candidate (lowest hours)
            if eligible_students:
                eligible_students.sort(key=lambda x: (x[0], random.random()))
                
                _, student = eligible_students[0]
                
                schedule[slot].append(student)
                student_hours[student] += 1
                availability_data[student][slot] = 'ASSIGNED'
                print(f"  --> ASSIGNED OK (Coverage): {student} in {slot}. Total hours: {student_hours[student]}")


    # --- PHASE 2B: Filling Priority (Add second student to reach SLOTS_PER_HOUR) ---
    print("\nPhase 2B: Filling remaining slots (Double Staffing) with 'OK'...")

    # Sort slots to ensure consistent assignment across runs
    slots_to_fill_second = sorted([slot for slot in slot_names if len(schedule[slot]) < SLOTS_PER_HOUR])
    
    for slot in slots_to_fill_second:
        # Check if the slot still needs more students (will be 1 if it has 1, or 2 if somehow still empty)
        needed = SLOTS_PER_HOUR - len(schedule[slot])
        
        if needed > 0:
            # Find eligible students for this slot (OK or MUST status, not yet full)
            eligible_students = []
            for student in students:
                status = availability_data[student].get(slot)
                
                # Must be 'OK' and not already assigned in this slot
                is_available_ok = status == 'OK'
                
                # Only proceed if the student is not assigned yet and is under their hour limit
                is_student_full = student_hours[student] >= MAX_HOURS_PER_STUDENT

                if is_available_ok and not is_student_full and student not in schedule[slot]:
                    priority_score = student_hours[student]
                    eligible_students.append((priority_score, student))

            # Assign the best candidates
            eligible_students.sort(key=lambda x: (x[0], random.random()))
            
            for i in range(min(needed, len(eligible_students))):
                _, student = eligible_students[i]
                
                schedule[slot].append(student)
                student_hours[student] += 1
                availability_data[student][slot] = 'ASSIGNED'
                print(f"  --> ASSIGNED OK (Double Staffing): {student} in {slot}. Total hours: {student_hours[student]}")


    # --- Output Formatting for Console and CSV (Long Format) ---
    schedule_records = []
    for slot, assigned_students in schedule.items():
        # Pad with empty strings if the slot is not full
        assigned_students.extend([''] * (SLOTS_PER_HOUR - len(assigned_students)))
        
        record = {'Time Slot': slot}
        for i, student in enumerate(assigned_students):
            record[f'Student {i+1}'] = student
        schedule_records.append(record)

    final_schedule_long_df = pd.DataFrame(schedule_records)
    
    # Create the final summary table
    summary_df = pd.DataFrame(student_hours.items(), columns=['Student', 'Assigned Hours'])
    summary_df['Goal Hours'] = MAX_HOURS_PER_STUDENT
    
    print("\n--- Scheduling Complete ---")
    print(f"Students with full hours (>= {MAX_HOURS_PER_STUDENT}): {len(summary_df[summary_df['Assigned Hours'] >= MAX_HOURS_PER_STUDENT])}/{len(students)}")
    
    return final_schedule_long_df, summary_df, schedule

def export_calendar_schedule(schedule_dict: Dict[str, List[str]], export_path: str):
    """
    Converts the schedule dictionary into the wide (calendar) format and exports to CSV.
    """
    
    # 1. Prepare data for wide format (Day columns, Time rows)
    calendar_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(str))
    
    # Split "Day Time - Time" into Day and Time
    for full_slot, students in schedule_dict.items():
        parts = full_slot.split(' ', 1)
        day = parts[0]
        time_slot = parts[1]
        
        # Combine student names into a single string, separated by newlines or a comma
        # Newlines (\n) work better for presentation within a single cell
        calendar_data[time_slot][day] = '\n'.join(students)
        
    # 2. Create DataFrame
    
    # Determine all unique time slots (rows) and days (columns)
    def sort_key(time_str):
        # time_str is in format '9 AM - 10 AM'. We take '9 AM'
        start_time_str = time_str.split(' - ')[0]
        
        # FIX: Check for "12 NOON" and convert it to "12 PM" for reliable parsing
        if start_time_str == "12 NOON":
            start_time_str = "12 PM"
            
        # Use a reliable format for parsing the time string
        return pd.to_datetime(start_time_str, format='%I %p').time()
        
    time_slots = sorted(calendar_data.keys(), key=sort_key)
    day_order = list(LAB_HOURS.keys())
    
    # Build the final table structure
    calendar_records = []
    for time_slot in time_slots:
        record = {'Start Time': time_slot.split(' - ')[0]} # Use just the start time for the first column
        for day in day_order:
            record[day] = calendar_data.get(time_slot, {}).get(day, '')
        calendar_records.append(record)
        
    calendar_df = pd.DataFrame(calendar_records)
    
    # 3. Export to CSV
    calendar_df.to_csv(export_path, index=False)
    print(f"\n--- Exported Calendar Schedule to {export_path} ---")

def export_student_schedule_list(schedule_dict: Dict[str, List[str]], filepath: str, max_hours: int):
    """
    Exports the schedule as a list of hours assigned to each student.
    Format: Student, Hour 1, Hour 2, ...
    """
    student_hours_map = defaultdict(list)
    
    # Populate map: Student -> [Slot 1, Slot 2, ...]
    for slot, students in schedule_dict.items():
        for student in students:
            if student: # Check if the slot was actually assigned
                student_hours_map[student].append(slot)
    
    # Build DataFrame records
    records = []
    
    # Create the column headers dynamically (e.g., 'Hour 1', 'Hour 2')
    hour_columns = [f'Hour {i+1}' for i in range(max_hours)]
    
    for student, slots in student_hours_map.items():
        record = {'Student': student}
        
        # Fill in assigned hours
        for i, slot in enumerate(slots):
            if i < max_hours: # Ensure we don't exceed the defined max columns
                record[hour_columns[i]] = slot
                
        # Fill remaining hour columns with empty string if the student has less than max_hours
        for i in range(len(slots), max_hours):
            record[hour_columns[i]] = ''
            
        records.append(record)

    student_summary_df = pd.DataFrame(records)
    
    # Ensure all required columns are present, even if a student has no hours
    required_cols = ['Student'] + hour_columns
    for col in required_cols:
        if col not in student_summary_df.columns:
            student_summary_df[col] = ''
            
    # Sort to ensure proper column order
    student_summary_df = student_summary_df[required_cols]

    # Export
    student_summary_df.to_csv(filepath, index=False)
    print(f"---Exported Student Summary List to {filepath}---")
    
    
if __name__ == '__main__':
    # 1. Define time slots based on lab hours
    all_slots = generate_time_slots()
    
    # 2. Load and prepare data
    availability_data_file = 'LabOp Timeslot Preference Selection Form - Filled.csv' # Use the final data file name
    availability_df, loaded_slot_names = load_data(availability_data_file)
    
    if availability_df is not None and not availability_df.empty:
        # 3. Create the optimized schedule
        schedule_long_df, summary_df, schedule_dict = create_schedule(availability_df, all_slots)
        
        # 4. Print the final results in a nice format (Long Format)
        print("\n" + "="*80)
        print("FINAL LAB SCHEDULE (LONG FORMAT)")
        print("="*80)
        # Using to_markdown for a clean, table-like output
        print(schedule_long_df.to_markdown(index=False))

        print("\n" + "="*80)
        print("STUDENT HOURS SUMMARY")
        print("="*80)
        print(summary_df.to_markdown(index=False))
        
        # 5. Export BOTH schedule formats to CSV files
        
        # Export 5a: Calendar Format (requested format)
        export_calendar_schedule(schedule_dict, 'LabOp_Schedule.csv')

        # Export 5b: Student Schedule List
        export_student_schedule_list(schedule_dict, 'LabOp_Student_Schedule.csv', max_hours=MAX_HOURS_PER_STUDENT)

        # Export 5c: Long Format (original format)
        schedule_long_df.to_csv('LabOp_Schedule_Long.csv', index=False)
        print("--- Exported Long Format Schedule to LabOp_Schedule_Long.csv ---")


        print(f"\nConfiguration: {SLOTS_PER_HOUR} students per hour, {MAX_HOURS_PER_STUDENT} max hours per student.")
