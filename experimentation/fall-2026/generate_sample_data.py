#!/usr/bin/env python3
"""Generate synthetic F26-format labop survey data for stress testing.

Produces a responses.csv-shaped dataframe using this semester's real 39-slot
Mon-Fri layout (10 AM - 6 PM Mon-Thu, 10 AM - 5 PM Fri), so it can be fed
straight into the production solver in src/schedule.py.

`must_have` is the TOTAL number of MUST-HAVE entries across the whole
dataset - each student gets at most one MUST-HAVE slot (mirroring
experimentation/spring-2026/experimentation_sub_repo/labop_distribution.py's
`--u` convention, and how real students actually behave: most submit zero
MUST-HAVEs, a handful submit exactly one). `unavailable` is an exact count of
UNAVAILABLE slots applied to every student.

An earlier version of this generator applied `must_have` as an exact
per-student count to ALL students, which saturates immediately: with 39
students spread over only 39 slots, even one MUST-HAVE each collides onto
some slot's 2-seat cap almost every time (birthday-paradox effect), so
`must_have=1` was ~always infeasible regardless of `unavailable`. The
total-across-dataset framing sweeps more informatively from "nobody cares" to
"everybody insists on a slot."

CLI usage:
  python generate_sample_data.py --students 39 --must-have 10 --unavailable 12 --seed 0 --out sample.csv
"""
from __future__ import annotations

import argparse
import os
import random
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from labop_common import (  # noqa: E402
    AVAILABLE,
    METADATA_COLUMNS,
    MUST_HAVE,
    PREFERENCE_COLUMN,
    UNAVAILABLE,
    build_slot_columns,
)

PREFERENCE_VALUES = ["Consecutive slots", "Spread out slots"]


def generate_dataframe(num_students, must_have, unavailable, seed=None):
    """Build one synthetic responses dataframe in the real F26 column layout.

    `must_have` students (chosen at random, without replacement) each get
    exactly one MUST-HAVE slot; every student gets exactly `unavailable`
    UNAVAILABLE slots; everything else is AVAILABLE.

    Raises ValueError if must_have > num_students (each student can have at
    most one MUST-HAVE here), if unavailable > total slots, or if a student
    who's due a MUST-HAVE has no non-UNAVAILABLE slot left to place it in.
    """
    slots = build_slot_columns()
    total_slots = len(slots)
    if must_have < 0 or unavailable < 0:
        raise ValueError("must_have and unavailable must be non-negative")
    if must_have > num_students:
        raise ValueError(f"must_have ({must_have}) cannot exceed num_students ({num_students})")
    if unavailable > total_slots:
        raise ValueError(f"unavailable ({unavailable}) exceeds total slots ({total_slots})")
    if unavailable == total_slots and must_have > 0:
        raise ValueError("no slots remain for a MUST-HAVE once every slot is UNAVAILABLE")

    rng = random.Random(seed)
    student_order = list(range(num_students))
    rng.shuffle(student_order)
    students_with_must_have = set(student_order[:must_have])

    rows = []
    for i in range(num_students):
        remaining = list(range(total_slots))
        rng.shuffle(remaining)
        unavailable_idx = set(remaining[:unavailable])

        must_idx = None
        if i in students_with_must_have:
            must_candidates = [idx for idx in remaining if idx not in unavailable_idx]
            if not must_candidates:
                raise ValueError(
                    f"student {i} has no slot left for a MUST-HAVE after {unavailable} UNAVAILABLEs"
                )
            must_idx = rng.choice(must_candidates)

        values = []
        for idx in range(total_slots):
            if idx == must_idx:
                values.append(MUST_HAVE)
            elif idx in unavailable_idx:
                values.append(UNAVAILABLE)
            else:
                values.append(AVAILABLE)

        row = {
            "ID": i + 1,
            "Start time": "",
            "Completion time": "",
            "Email": f"student{i + 1}@example.edu",
            "Name": f"Student {i + 1}",
            "Last modified time": "",
            "Last name": f"Last{i + 1}",
            "First name": f"First{i + 1}",
            PREFERENCE_COLUMN: rng.choice(PREFERENCE_VALUES),
        }
        row.update(dict(zip(slots, values)))
        rows.append(row)

    columns = METADATA_COLUMNS + [PREFERENCE_COLUMN] + slots
    return pd.DataFrame(rows, columns=columns)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--students", type=int, default=39, help="number of students to generate")
    p.add_argument("--must-have", type=int, default=5, help="total MUST-HAVE entries across the dataset (max 1/student)")
    p.add_argument("--unavailable", type=int, default=12, help="exact UNAVAILABLE slots per student")
    p.add_argument("--seed", type=int, default=0, help="random seed")
    p.add_argument("--out", type=str, default=None, help="output CSV path")
    return p.parse_args()


def main():
    args = parse_args()
    df = generate_dataframe(args.students, args.must_have, args.unavailable, seed=args.seed)
    out = args.out or f"sample_students{args.students}_must{args.must_have}_unavail{args.unavailable}_s{args.seed}.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} students x {len(build_slot_columns())} slots to {out}")


if __name__ == "__main__":
    main()
