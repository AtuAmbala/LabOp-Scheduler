# LabOp-Scheduler

This Python script is designed to automate the process of creating a weekly staffing schedule for a lab based on student availability and defined lab hours.

It reads student preference data from a CSV file, cleans the data, and then attempts to create an **optimized schedule** that prioritizes required (MUST) assignments and aims to provide fair coverage across all lab hours while adhering to staffing limits.

---

## 🚀 Quick Start

1.  **Input File:** Ensure your student availability data is in a CSV file named:
    `LabOp Timeslot Preference Selection Form - Filled.csv`
2.  **Run:** Execute the script from your terminal:
    ```bash
    python LabOp_Optimizer.py
    ```
3.  **Output:** The script prints the schedule and summary to the console, and generates the following two CSV files in the same directory:
    * **`LabOp_Schedule.csv`**: The final schedule in a **calendar (wide) format** (Time as rows, Day as columns).
    * **`LabOp_Schedule_Long.csv`**: The final schedule in a **long format** (Time Slot as rows, Student columns).

---

## ⚙️ Configuration Variables

The scheduling process is controlled by the following global variables defined at the beginning of the script:

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `SLOTS_PER_HOUR` | The **number of students** required to staff each 1-hour lab session. | `2` |
| `MAX_HOURS_PER_STUDENT` | The **maximum number of hours** any student should be assigned for the week. | `2` |

The script also uses the **`LAB_HOURS`** dictionary to define the operational hours for the week:

| Day | Hours (24hr) | Note |
| :--- | :--- | :--- |
| Monday-Thursday | `(9, 21)` | 9 AM to 9 PM |
| Friday | `(9, 16)` | 9 AM to 4 PM |
| Saturday | `(12, 16)` | 12 PM to 4 PM |
| Sunday | `(12, 17)` | 12 PM to 5 PM |

---

## 📝 Scheduling Logic (The Three Phases)

The script uses a weighted, multi-phase assignment strategy to ensure all constraints are met and fairness is maintained:

### Phase 1: MUST Assignments (Highest Priority)
* **Goal:** Fulfill all slots where a student indicated **`MUST-SELECT`**.
* **Constraint Check:** An assignment is *only* made if the student is under `MAX_HOURS_PER_STUDENT` and the slot is under `SLOTS_PER_HOUR`.
* *Note: MUST-SELECT slots are processed first and assigned randomly if multiple apply to a student.*

### Phase 2A: Coverage Priority (Minimum Staffing)
* **Goal:** Ensure **every single time slot** has at least **one student** assigned (if possible).
* **Availability Used:** Only students with **`OK`** availability are considered for this phase.
* **Tie-breaker:** Prioritizes students with the **fewest** currently assigned hours (promoting fair initial coverage).

### Phase 2B: Filling Priority (Double Staffing)
* **Goal:** Assign a second student (or fill any remaining open spots) up to the `SLOTS_PER_HOUR` limit.
* **Availability Used:** Only students with **`OK`** availability who are *not already assigned* to that specific slot are considered.
* **Tie-breaker:** Prioritizes students with the **fewest** currently assigned hours.

---

## 📊 Data Pre-processing (`load_data`)

The script includes critical logic to handle the common formatting issues of form-generated CSV files:

### 1. Column Name Normalization
The function `_generate_csv_column_map` contains extensive logic to map the often messy and inconsistent CSV column headers (e.g., `'12 NOON - 1 PM2'`, `'Sunday 12 NOON - 1 PM6'`) into a **clean, consistent internal format** (e.g., `'Tuesday 12 PM - 1 PM'`). This ensures accurate alignment of availability data.

### 2. Student Identifier
The script looks for a column named **`Name`**. If not found, it defaults to using the **first column** of the CSV as the unique student identifier.

### 3. Availability Code Cleansing
All availability preference strings are normalized using the **`AVAILABILITY_MAP`** for consistency:
* `MUST-SELECT` $\rightarrow$ `MUST`
* `CANNOT-SELECT` $\rightarrow$ `CANNOT`
* Any other input (including 'OK') $\rightarrow$ `OK`
