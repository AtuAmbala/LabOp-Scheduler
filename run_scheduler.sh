#!/usr/bin/env bash
set -e
RESPONSES="responses.csv"
SCHEDULE_STU="schedule_by_students.csv"
SCHEDULE_SLOT="schedule_by_slot.csv"
echo "Checking responses..."
python check_responses.py "$RESPONSES"
echo "Running scheduler..."
python schedule.py "$RESPONSES" "$SCHEDULE_STU"
echo "Checking output..."
python3 check_output.py "$RESPONSES" "$SCHEDULE_STU" "$SCHEDULE_SLOT"
echo "Done!"
