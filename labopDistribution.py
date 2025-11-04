"""Generate random guard availability CSVs for labop scheduling.

python labopDistribution.py --l 67 --m 50 --r 15 --u 1 --out outputfolder --seed 200 --num-sets 50

    --l = number of slots
    --m = number of guards
    --r = number of rejects (CANNOT-SELECT) per guard
    --u = total number of MUST-SELECT entries in the entire dataset (each guard max 1)
    --out = output base directory
    --num-sets = how many random sets to generate (each will use seed+i)

Creates a folder with m per-guard CSV files and a combined CSV with the same format as the example.

Each guard will have exactly `r` CANNOT-SELECT entries. The CLI option `--u` now specifies
the total number of MUST-SELECT entries across the entire dataset (each guard may have at most one).
All other slots are OK.

Usage: run the script as a module or call generate_dataset() from other code. Parameters are configurable at top-level or via CLI.
"""


from __future__ import annotations

import csv
import math
import os
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Tuple


def gen_slot_times(l: int, start_date: str = "10/01/25") -> List[Tuple[str, str]]:
    """Generate dummy start/completion times for l slots.

    Returns list of (start_str, completion_str) in the same format as the sample CSV (M/D/YY H:M).
    We'll space slots by 1 hour starting at 9 AM of start_date.
    """
    base = datetime.strptime(start_date + " 09:00", "%m/%d/%y %H:%M")
    slots = []
    for i in range(l):
        st = base + timedelta(hours=i)
        en = st + timedelta(hours=1)
        slots.append((st.strftime("%m/%d/%y %H:%M"), en.strftime("%m/%d/%y %H:%M")))
    return slots


def make_guard_row(guard_idx: int, l: int, r: int, has_must: bool = False, seed: int | None = None) -> Tuple[List[str], str, str, str, str, str, str]:
    """Create a single guard CSV row.

    Each guard will get exactly `r` CANNOT-SELECT entries. If `has_must` is True,
    the guard will get exactly one MUST-SELECT chosen from the remaining slots.

    Returns: (cells_for_slots, id, start time, completion time, email, last name, first name)
    cells_for_slots length == l and contains 'MUST-SELECT','CANNOT-SELECT','OK'
    """
    # Use per-guard determinism when seed provided
    if seed is not None:
        random.seed(seed + guard_idx)
    slots = list(range(l))
    # pick r slots to be CANNOT-SELECT
    cannot = set(random.sample(slots, r)) if r > 0 else set()
    remaining = [s for s in slots if s not in cannot]
    must = set()
    if has_must:
        if len(remaining) == 0:
            raise ValueError(f"Guard {guard_idx}: cannot assign MUST-SELECT; no remaining slots after rejects")
        # pick a single MUST-SELECT slot
        must = set(random.sample(remaining, 1))

    cells = []
    for i in range(l):
        if i in must:
            cells.append("MUST-SELECT")
        elif i in cannot:
            cells.append("CANNOT-SELECT")
        else:
            cells.append("OK")

    # Minimal metadata
    gid = str(guard_idx + 1)
    email = f"guard{gid}@example.edu"
    lname = f"Last{gid}"
    fname = f"First{gid}"
    # use same start/completion for file-level timestamp placeholder
    start_time = datetime.now().strftime("%m/%d/%y %H:%M")
    completion_time = (datetime.now() + timedelta(minutes=2)).strftime("%m/%d/%y %H:%M")
    return cells, gid, start_time, completion_time, email, f"{lname}", f"{fname}"


def write_combined_csv(output_path: str, slots: List[Tuple[str, str]], guard_rows: List[Tuple[List[str], str, str, str, str, str, str]]):
    """Write a single combined CSV with header matching sample file."""
    l = len(slots)
    # create slot column names similar to sample: '9 AM - 10 AM', etc. We'll just use 'Slot 1'..'Slot l'
    slot_names = [f"Slot {i+1}" for i in range(l)]
    header = [
        "Id",
        "Start time",
        "Completion time",
        "Email",
        "Name",
        "Last name",
        "First name",
    ] + slot_names

    with open(output_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for cells, gid, start_time, completion_time, email, lname, fname in guard_rows:
            row = [gid, start_time, completion_time, email, lname, lname, fname] + cells
            writer.writerow(row)

def generate_dataset(l: int = 67, m: int = 50, r: int = 10, total_musts: int = 1, k_min: int = 1, k_max: int = 3, s: int = 3, out_dir: str = "outputs", seed: int | None = 42) -> str:
    """Generate dataset and return path to output directory.

    `total_musts` is the total number of MUST-SELECT entries across the dataset.
    Each guard may have at most one MUST-SELECT, so total_musts must be <= m.

    This creates a folder under out_dir named dataset_r{r}_u{total_musts}_m{m}_l{l}.
    """
    if total_musts > m:
        raise ValueError("total_musts cannot exceed number of guards m")
    if r >= l and total_musts > 0:
        raise ValueError("r is too large: no remaining slots available to assign MUST-SELECTs")

    random.seed(seed)
    slots = gen_slot_times(l)
    guard_rows = []

    # Choose which guards will receive a MUST-SELECT (each at most one)
    must_guard_indices = set(random.sample(range(m), total_musts)) if total_musts > 0 else set()

    for gi in range(m):
        has_must = gi in must_guard_indices
        cells, gid, st, ct, email, lname, fname = make_guard_row(gi, l, r, has_must, seed)
        guard_rows.append((cells, gid, st, ct, email, lname, fname))

    # Use a single folder for the parameter set (all seeds will write into this folder)
    folder = os.path.join(out_dir, f"dataset_r{r}_u{total_musts}_m{m}_l{l}")
    os.makedirs(folder, exist_ok=True)
    # Name the CSV with the seed so multiple sets land in the same folder
    combined_path = os.path.join(folder, f"combined_s{seed}.csv")
    write_combined_csv(combined_path, slots, guard_rows)

    # basic verification info
    print(f"Wrote combined CSV to: {combined_path}")
    return folder


def parse_args():
    p = argparse.ArgumentParser(description="Generate random guard availability CSV dataset")
    p.add_argument("--l", type=int, default=67, help="number of slots")
    p.add_argument("--m", type=int, default=50, help="number of guards")
    p.add_argument("--r", type=int, default=15, help="number of rejects (CANNOT-SELECT) per guard")
    p.add_argument("--u", type=int, default=1, help="total number of MUST-SELECT entries across the dataset (each guard max 1)")
    p.add_argument("--num-sets", type=int, default=1, help="how many random sets to generate (each will use seed+i)")
    p.add_argument("--out", type=str, default="outputs", help="output base directory")
    p.add_argument("--seed", type=int, default=42, help="random seed")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # generate multiple datasets if requested
    folders = []
    # create a single folder and write multiple CSVs in it, named by seed
    target_folder = os.path.join(args.out, f"dataset_r{args.r}_u{args.u}_m{args.m}_l{args.l}")
    os.makedirs(target_folder, exist_ok=True)
    created_files = []
    for i in range(args.num_sets):
        s = args.seed + i if args.seed is not None else None
        # pass the same out_dir but generate_dataset will write into the parameter folder and name by seed
        folder = generate_dataset(l=args.l, m=args.m, r=args.r, total_musts=args.u, out_dir=args.out, seed=s)
        # collect the csv path
        csv_path = os.path.join(folder, f"combined_s{s}.csv")
        created_files.append(csv_path)
    print("Done. Created files:")
    for fpath in created_files:
        print(" -", fpath)
