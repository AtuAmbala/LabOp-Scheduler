#!/usr/bin/env python3
"""Sweep MUST-HAVE / UNAVAILABLE counts to find where the exact-2-slot,
39-student x 39-slot labop schedule stops being solvable.

Imports the real production solver from src/schedule.py (build_and_solve), so
results reflect the actual scheduler used to build the real schedule, not a
re-implementation that could drift out of sync with it.

`must_have` is the total number of MUST-HAVE entries across the whole
39-student dataset (each student gets at most one - see
generate_sample_data.py for why). `unavailable` is an exact per-student count
applied to every student. For each (must_have, unavailable) combination,
generates `--trials` random datasets (different seeds) and records the
feasibility rate - the fraction that solved to Optimal. Writes a CSV grid and
(if matplotlib is available) a heatmap PNG.

Usage:
  python stress_test.py \
      --must-have-values 0,5,10,15,20,25,30,35,39 \
      --unavailable-values 0,5,10,15,20,25,30,33,35,36 \
      --trials 8 \
      --out-csv results/feasibility_grid.csv \
      --out-plot results/feasibility_heatmap.png

Use --mode SPREAD (default) for these sweeps: it solves far faster than
CONTIGUOUS and feasibility doesn't depend on the contiguity objective, only on
the hard MUST-HAVE/UNAVAILABLE/exactly-2 constraints.
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, THIS_DIR)

from schedule import build_and_solve  # noqa: E402  (production solver)
from generate_sample_data import generate_dataframe  # noqa: E402


def sweep(must_have_values, unavailable_values, trials, num_students, time_limit, mode):
    records = []
    total_runs = len(must_have_values) * len(unavailable_values) * trials
    done = 0
    for must_have, unavailable in itertools.product(must_have_values, unavailable_values):
        feasible_count = 0
        attempted = 0
        skipped = 0
        for trial in range(trials):
            seed = must_have * 1_000_000 + unavailable * 1_000 + trial
            try:
                df = generate_dataframe(num_students, must_have, unavailable, seed=seed)
            except ValueError:
                skipped += 1
                continue
            attempted += 1
            status, _, _ = build_and_solve(df, mode=mode, time_limit=time_limit, msg=0)
            if status == "Optimal":
                feasible_count += 1
            done += 1
            print(
                f"[{done}/{total_runs}] must_have={must_have} unavailable={unavailable} "
                f"trial={trial} -> {status}"
            )
        rate = (feasible_count / attempted) if attempted else float("nan")
        records.append(
            {
                "must_have": must_have,
                "unavailable": unavailable,
                "trials": attempted,
                "feasible": feasible_count,
                "feasibility_rate": rate,
                "skipped_impossible_to_generate": skipped,
            }
        )
    return pd.DataFrame(records)


def plot_heatmap(df, out_path):
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not installed; skipping heatmap (grid CSV was still written).")
        return

    must_values = sorted(df["must_have"].unique())
    unavail_values = sorted(df["unavailable"].unique())
    grid = np.full((len(must_values), len(unavail_values)), float("nan"))
    for _, row in df.iterrows():
        i = must_values.index(row["must_have"])
        j = unavail_values.index(row["unavailable"])
        grid[i, j] = row["feasibility_rate"]

    fig, ax = plt.subplots(figsize=(max(6, len(unavail_values) * 0.6), max(4, len(must_values) * 0.6)))
    im = ax.imshow(grid, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(unavail_values)))
    ax.set_xticklabels(unavail_values)
    ax.set_yticks(range(len(must_values)))
    ax.set_yticklabels(must_values)
    ax.set_xlabel("UNAVAILABLE slots per student")
    ax.set_ylabel("Total MUST-HAVE entries across the dataset")
    ax.set_title("Feasibility rate (39 students x 39 slots, exactly 2 slots/student)")
    for i in range(len(must_values)):
        for j in range(len(unavail_values)):
            val = grid[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", color="black", fontsize=8)
    fig.colorbar(im, ax=ax, label="Feasibility rate")
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path)
    print(f"Saved heatmap to {out_path}")


def parse_int_list(s):
    return [int(x) for x in s.split(",") if x.strip() != ""]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--must-have-values",
        type=parse_int_list,
        default=[0, 5, 10, 15, 20, 25, 30, 35, 39],
        help="total MUST-HAVE entries across the dataset (max 1/student)",
    )
    p.add_argument(
        "--unavailable-values",
        type=parse_int_list,
        default=[0, 5, 10, 15, 20, 25, 30, 33, 35, 36],
        help="exact UNAVAILABLE slots per student",
    )
    p.add_argument("--trials", type=int, default=3, help="random datasets per (must_have, unavailable) cell")
    p.add_argument("--students", type=int, default=39)
    p.add_argument("--time-limit", type=int, default=30, help="per-solve CBC time limit, seconds")
    p.add_argument(
        "--mode",
        choices=["CONTIGUOUS", "SPREAD"],
        default="SPREAD",
        help="objective mode; SPREAD is recommended for feasibility sweeps (much faster)",
    )
    p.add_argument("--out-csv", type=str, default=os.path.join(THIS_DIR, "results", "feasibility_grid.csv"))
    p.add_argument("--out-plot", type=str, default=os.path.join(THIS_DIR, "results", "feasibility_heatmap.png"))
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    df = sweep(args.must_have_values, args.unavailable_values, args.trials, args.students, args.time_limit, args.mode)
    df.to_csv(args.out_csv, index=False)
    print(f"\nSaved feasibility grid to {args.out_csv}")
    print(df.to_string(index=False))
    plot_heatmap(df, args.out_plot)


if __name__ == "__main__":
    main()
