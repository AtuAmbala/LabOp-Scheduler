# LabOp Scheduler

This repo contains a program that take student availability responses, build a schedule, and verify the results.

## How to Use

1. Create a new conda environment and install the dependencies using: `conda env create -f environment.yml`
2. Activate the environment using: `conda activate labop-scheduler`
3. Download the survey responses as a CSV file and save it in the root directory of the project as: responses.csv
4. Run the pipeline using: `./run_scheduler.sh`
5. The script will:

   - Check the responses (`check_responses.py`)
   - Build the schedule (`schedule.py`)
   - Validate the output (`check_output.py`)

5. If the problem is feasible, you'll get two output files:

- `schedule_by_student.csv`
- `schedule_by_slot.csv`

If it's infeasible, the scheduler will tell you.

That’s it. Keep the CSV in the root directory and run the script whenever you want a new schedule.

The experimentation-sub-repo is where we test different algorithms and approaches to solve the scheduling problem. It does not pertain to the user unless they want to contribute or provide feedback.

# How it works:

## check_responses.py
This script checks your raw responses.csv before scheduling to make sure nothing breaks the solver.

It verifies:

No student has more than 3 MUST-HAVE slots.

Total number of MUST-HAVEs across all students is below your threshold (e.g., 15).

No student has more than 20 UNAVAILABLE slots.

If anything violates these rules, it prints out exactly who and what went wrong.

## schedule.py
This is implemented using an ILP scheduler.

It builds a PuLP optimization model based on responses that assigns each student to 2–3 slots, ensures each slot gets up to 2 students, enforces these hard constraints:

MUST-HAVE → student must be assigned that slot

UNAVAILABLE → student cannot be assigned that slot

If an optimal schedule exists, it outputs two schedules, one for each student, and the other for each slot.

## check_output.py

This script double-checks the scheduler output to ensure everything is valid.

It verifies:

Student-level checks:

Every student has unique slots (no duplicates)

All MUST-HAVE constraints are satisfied

All UNAVAILABLE constraints are respected

Slot-level checks:

Every slot has unique students

No slot accidentally assigns the same student twice

If anything is wrong, it prints the exact violations.

