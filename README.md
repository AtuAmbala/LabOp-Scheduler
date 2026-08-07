# LabOp Scheduler

This repo contains a program that takes student availability responses, builds a schedule, and verifies the results.

## Layout

- `src/` - the production pipeline (`config.py`, `convert_xlsx_to_csv.py`, `check_responses.py`, `schedule.py`, `check_output.py`, `labop_common.py`)
- `scripts/` - `run_scheduler.sh`, the entry point that runs the pipeline end to end
- `output-schedule/` - where the pipeline writes `schedule_by_students.csv` / `schedule_by_slot.csv`
- `experimentation/fall-2026/` - current-semester stress-test tooling (synthetic data generator + feasibility sweep + tests) for finding safe MUST-HAVE/UNAVAILABLE limits
- `experimentation/spring-2026/` - prior semester's experimentation (`experimentation_sub_repo`, `copilot-testing`); kept for reference, not part of the production pipeline

## This semester's constraints (Fall 2026)

Labop hours are **10 AM - 6 PM Monday-Thursday** and **10 AM - 5 PM Friday**, which gives exactly **39 one-hour slots** (8+8+8+8+7). With **39 students** each working **exactly 2 hours** and **2 labops required per slot**, the numbers match exactly (39 x 2 = 78 = 39 x 2) - a fully-subscribed, feasible schedule uses every student-hour and every slot-seat with nothing left over.

Because of this, `src/schedule.py` assigns each student **exactly 2** slots (not a 2-3 range like in past semesters). A student with more than 2 MUST-HAVE slots can never be satisfied, so `src/check_responses.py` now flags any student with more than 2 MUST-HAVEs.

The survey now also asks each student whether they prefer consecutive or spread-out slots. That answer is captured in the data but **not yet used by the solver** - the global `SCHEDULE_MODE` setting in `config.py` still applies the same contiguous-vs-spread objective to everyone. Using the per-student answer instead is a natural follow-up if it's wanted.

See `experimentation/fall-2026/README.md` for the tooling used to figure out what MUST-HAVE/UNAVAILABLE limits keep the schedule reliably feasible.

## How to Use

1. Create a new conda environment and install the dependencies using: `conda env create -f environment.yml`
2. Activate the environment using: `conda activate labop-scheduler`
3. Download the survey responses as an Excel (.xlsx) export.
4. If you want to optimize for contiguous slots, edit `src/config.py` and set `SCHEDULE_MODE = "CONTIGUOUS"`; otherwise, set `SCHEDULE_MODE = "SPREAD"`.
5. Run the pipeline, pointing it at your .xlsx: `./scripts/run_scheduler.sh path/to/survey-export.xlsx`

   (Already have a `responses.csv` in the root and don't need to convert anything? Just run `./scripts/run_scheduler.sh` with no argument.)

6. The script will:

   - Convert the .xlsx to `responses.csv` in the repo root (`src/convert_xlsx_to_csv.py`), if an .xlsx was given
   - Check the responses (`src/check_responses.py`)
   - Build the schedule (`src/schedule.py`)
   - Validate the output (`src/check_output.py`)

7. If the problem is feasible, you'll get two output files in `output-schedule/`:

- `schedule_by_students.csv`
- `schedule_by_slot.csv`

If it's infeasible, the scheduler will tell you.

That's it. Run the script whenever you want a new schedule.

# How it works:

## src/config.py
This file currently has one parameter: `SCHEDULE_MODE`, which can be set to either `CONTIGUOUS` or `SPREAD`. `CONTIGUOUS` tries to assign students to back-to-back slots within the same day, while `SPREAD` ignores the contiguity constraint and finds any solution (which tends to be rather spread out).

## src/convert_xlsx_to_csv.py
CLI: `python src/convert_xlsx_to_csv.py path/to/survey-export.xlsx --output responses.csv`

Converts a Forms/Sheets .xlsx survey export to the `responses.csv` the rest of the pipeline reads. With no arguments, converts the example `F26-TestSurveyData_39_Dummy.xlsx` in the repo root.

## src/labop_common.py
Shared constants/helpers describing this semester's survey layout: the 39 slot column names in Forms export order, which columns are metadata vs. slots, per-day slot groupings, and the exactly-2-slots-per-student / 2-students-per-slot constants. Both the production scripts and the `experimentation/fall-2026` tooling import from here so they can't drift out of sync.

## src/check_responses.py
CLI: `python src/check_responses.py responses.csv`

This script checks your raw responses.csv before scheduling to make sure nothing breaks the solver.

It verifies:

- No student has more than 2 MUST-HAVE slots (a student can only ever be assigned 2 slots total).
- No student has more than `MAX_UNAVAILABLE_PER_STUDENT_WARNING` UNAVAILABLE slots (tune this constant using `experimentation/fall-2026`'s feasibility sweep).
- No slot has more than 2 MUST-HAVEs, and every slot has at least 2 non-UNAVAILABLE students.

If anything violates these rules, it prints out exactly who and what went wrong.

## src/schedule.py
CLI: `python src/schedule.py responses.csv output-schedule/schedule.csv`

This is implemented using an ILP scheduler (also importable as `build_and_solve(df, mode=..., time_limit=..., msg=...)` for reuse, e.g. by the fall-2026 stress test).

It builds a PuLP optimization model based on responses that assigns each student to **exactly 2** slots, ensures each slot gets **exactly 2** students, and enforces these hard constraints:

- MUST-HAVE -> student must be assigned that slot
- UNAVAILABLE -> student cannot be assigned that slot

If an optimal schedule exists, it outputs two schedules, one for each student, and the other for each slot.

## src/check_output.py

CLI: `python src/check_output.py responses.csv output-schedule/schedule_by_students.csv output-schedule/schedule_by_slot.csv`

This script double-checks the scheduler output to ensure everything is valid.

It verifies:

Student-level checks:

- Every student has unique slots (no duplicates)
- All MUST-HAVE constraints are satisfied
- All UNAVAILABLE constraints are satisfied

Slot-level checks:

- Every slot has unique students
- No slot accidentally assigns the same student twice

If anything is wrong, it prints the exact violations.
