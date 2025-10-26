#!/usr/bin/env bash
# Run optimizer + tester for each combined_s*.csv in sample_data_labops
# Prints a single summary line per input file: dir: filename > CHECK1: status, CHECK2: status, CHECK3: status, CHECK4: status

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_ROOT="$ROOT_DIR/sample_data_labops"
shopt -s globstar nullglob
for f in "$DATA_ROOT"/**/combined_s*.csv; do
    filename=$(basename "$f")
    parent_dir=$(basename "$(dirname "$f")")
    parent_dir="${parent_dir:-.}"
    echo "Processing: $parent_dir/$filename"
    if optimizer_out=$(python "$ROOT_DIR/LabOp_Optimizer_sifat.py" "$f" 2>&1); then
        optimizer_rc=0
    else
        optimizer_rc=$?
    fi

    if [ "$optimizer_rc" -ne 0 ]; then
        if echo "$optimizer_out" | grep -iq "not possible"; then
            echo "$parent_dir: $filename > OPTIMIZER: NOT_POSSIBLE"
        else
            echo "$parent_dir: $filename > OPTIMIZER: ERROR"
            echo "  Optimizer output: $(echo "$optimizer_out" | head -n 3 | tr '\n' ' ' )"
        fi
        continue
    fi
    STUD_SCHED="$ROOT_DIR/LabOp_Student_Schedule_sifat.csv"
    if [ ! -f "$STUD_SCHED" ]; then
        if [ -f "LabOp_Student_Schedule_sifat.csv" ]; then
            STUD_SCHED="$(pwd)/LabOp_Student_Schedule_sifat.csv"
        else
            echo "$parent_dir: $filename > OPTIMIZER: OK, but missing student schedule output"
            continue
        fi
    fi
    if tester_out=$(python "$ROOT_DIR/test_scheduler.py" "$f" "$STUD_SCHED" 2>&1); then
        tester_rc=0
    else
        tester_rc=$?
    fi

    c1=$(echo "$tester_out" | grep -E '^CHECK1:' || true)
    c2=$(echo "$tester_out" | grep -E '^CHECK2:' || true)
    c3=$(echo "$tester_out" | grep -E '^CHECK3:' || true)
    c4=$(echo "$tester_out" | grep -E '^CHECK4:' || true)
    s1=$(echo "$c1" | awk -F': ' '{print $2}' | tr -d '\n')
    s2=$(echo "$c2" | awk -F': ' '{print $2}' | tr -d '\n')
    s3=$(echo "$c3" | awk -F': ' '{print $2}' | tr -d '\n')
    s4=$(echo "$c4" | awk -F': ' '{print $2}' | tr -d '\n')

    echo "$parent_dir: $filename > OPTIMIZER: OK, CHECK1: ${s1:-ERROR}, CHECK2: ${s2:-ERROR}, CHECK3: ${s3:-ERROR}, CHECK4: ${s4:-ERROR}"
done