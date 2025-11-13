# LabOp Scheduler

This repo contains a program that take student availability responses, build a schedule, and verify the results.

## How to Use

1. Create a new conda environment and install the dependencies using: `conda env create -f environment.yml`
2. Activate the environment using: `conda activate labop-scheduler`
3. Save the responses file in the **root directory** as: responses.csv
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
