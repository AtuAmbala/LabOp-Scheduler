#!/usr/bin/env python3
"""Convert a labop survey Excel export (Forms/Sheets download) to responses.csv.

With no arguments, converts this semester's example file
F26-TestSurveyData_39_Dummy.xlsx (repo root) to responses.csv (repo root) -
the file scripts/run_scheduler.sh reads. Pass a different .xlsx to convert a
real survey download instead.

Usage:
  python src/convert_xlsx_to_csv.py [input.xlsx] [--output responses.csv] [--sheet NAME_OR_INDEX]
"""
import argparse
import os
import sys

import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEFAULT_INPUT = os.path.join(REPO_ROOT, "F26-TestSurveyData_39_Dummy.xlsx")
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "responses.csv")


def convert(input_path, output_path, sheet_name=0):
    df = pd.read_excel(input_path, sheet_name=sheet_name)
    df.to_csv(output_path, index=False)
    return df


def _sheet_arg(value):
    try:
        return int(value)
    except ValueError:
        return value


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "input",
        nargs="?",
        default=DEFAULT_INPUT,
        help=f"source .xlsx (default: {os.path.relpath(DEFAULT_INPUT, REPO_ROOT)})",
    )
    p.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"destination CSV (default: {os.path.relpath(DEFAULT_OUTPUT, REPO_ROOT)})",
    )
    p.add_argument("--sheet", type=_sheet_arg, default=0, help="sheet name or index to read (default: first sheet)")
    return p.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    df = convert(args.input, args.output, sheet_name=args.sheet)
    print(f"Wrote {len(df)} rows x {len(df.columns)} columns from {args.input} to {args.output}")


if __name__ == "__main__":
    main()
