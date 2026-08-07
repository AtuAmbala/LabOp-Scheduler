#!/usr/bin/env bash
# Usage: ./scripts/run_scheduler.sh [path/to/survey-export.xlsx]
#   With no argument, uses the existing responses.csv in the repo root.
#   With an .xlsx argument, converts it to responses.csv first (overwriting
#   any existing one), then runs the pipeline.
set -e
cd "$(cd "$(dirname "$0")/.." && pwd)"

RESPONSES="responses.csv"
SCHEDULE="output-schedule/schedule.csv"
SCHEDULE_STU="output-schedule/schedule_by_students.csv"
SCHEDULE_SLOT="output-schedule/schedule_by_slot.csv"

mkdir -p output-schedule

if [ -n "$1" ]; then
  echo "Converting $1 to $RESPONSES..."
  python src/convert_xlsx_to_csv.py "$1" --output "$RESPONSES"
fi

echo "Checking responses..."
python src/check_responses.py "$RESPONSES"
echo "Running scheduler..."
python src/schedule.py "$RESPONSES" "$SCHEDULE"
echo "Checking output..."
python src/check_output.py "$RESPONSES" "$SCHEDULE_STU" "$SCHEDULE_SLOT"
echo "Done!"
