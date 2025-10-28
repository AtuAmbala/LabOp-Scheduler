#!/usr/bin/env bash

# how to use: ./run_all.sh /path/to/input_dir /path/to/output_dir [logfile]
input_dir="${1:-.}"                 # where to search for CSVs
output_dir="${2:-./outputs}"        # where to save all assignment results
log="${3:-results.log}"             # log file name
: > "$log"                          # clear log file

mkdir -p "$output_dir"
mapfile -t csv_files < <(find "$input_dir" -type f -name "*.csv")

if [ ${#csv_files[@]} -eq 0 ]; then
  echo "No CSV files found in $input_dir"
  exit 1
fi

count=0
total=${#csv_files[@]}
for f in "${csv_files[@]}"; do
  ((count++))
  rel_path="${f#$input_dir/}"                              
  rel_dir="$(dirname "$rel_path")"
  mkdir -p "$output_dir/$rel_dir"                          

  base="$(basename "${f%.*}")"
  out="$output_dir/$rel_dir/${base}_assignment.csv"

  echo "[$count/$total] Processing: $f"
  msg=$(python LabOp_Optimizer_sifat.py "$f" "$out" 2>&1)

  if echo "$msg" | grep -q 'NO OPTIMAL ASSIGNMENT'; then
    echo "$f,Infeasible" >> "$log"
  elif [ -s "$out" ]; then
    echo "$f,Optimal" >> "$log"
  else
    echo "$f,Unknown" >> "$log"
  fi
done

echo "Finished. Results saved to $log and outputs in $output_dir"
