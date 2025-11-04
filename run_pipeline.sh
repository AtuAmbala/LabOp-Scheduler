#!/usr/bin/env bash

# how to use: ./run_pipeline.sh [input_dir]
# Defaults: input_dir defaults to ./sample_data_labops (script will only search that folder)
# Outputs are written into ./sample_schedule_assignments (script will NOT create this dir)
input_dir="${1:-./sample_data_labops}"                 # where to search for CSVs (defaults to sample_data_labops)
output_dir="./sample_schedule_assignments"              # fixed output dir (do NOT auto-create)
log="${2:-results.log}"                                 # log file name (optional second arg)
: > "$log"                                              # clear log file


if [ ! -d "$output_dir" ]; then
  echo "Output directory $output_dir does not exist. Not creating it per configuration. Exiting."
  exit 1
fi

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

  base="$(basename "${f%.*}")"
  if [ "$rel_dir" = "." ]; then
    prefix=""
  else
    prefix="${rel_dir//\//__}_"
  fi

  out="$output_dir/${prefix}${base}_assignment.csv"

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
