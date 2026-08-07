#!/usr/bin/env python3
"""
Usage:
  python plot_results.py results.log --out-img summary.png --out-csv summary.csv

"""
from collections import defaultdict
import argparse
import os
import sys
import math
import pandas as pd
import matplotlib.pyplot as plt

def parse_log(path):
    results = []
    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if "," not in line:
                continue
            path_part, status = line.rsplit(',', 1)
            path_part = path_part.strip()
            status = status.strip()
            parent = os.path.dirname(path_part)
            if parent == "":
                subdir = os.path.basename(path_part)
            else:
                subdir = os.path.basename(parent.rstrip(os.sep))
            results.append((subdir, status))
    return results


def aggregate(results):
    agg = defaultdict(lambda: {"Optimal": 0, "Infeasible": 0, "Other": 0})
    for subdir, status in results:
        if status == "Optimal":
            agg[subdir]["Optimal"] += 1
        elif status == "Infeasible":
            agg[subdir]["Infeasible"] += 1
        else:
            agg[subdir]["Other"] += 1
    rows = []
    for subdir, counts in sorted(agg.items()):
        opt = counts.get("Optimal", 0)
        inf = counts.get("Infeasible", 0)
        total = opt + inf
        pct = (100.0 * opt / total) if total > 0 else float('nan')
        rows.append({
            "dataset_subdir": subdir,
            "optimal": opt,
            "infeasible": inf,
            "percent_optimal": pct,
            "other": counts.get("Other", 0),
            "total_opt_inf": total,
        })
    df = pd.DataFrame(rows)
    df = df.sort_values(by=["percent_optimal", "dataset_subdir"], ascending=[False, True]).reset_index(drop=True)
    return df


def plot_df(df, out_img):
    labels = df['dataset_subdir'].astype(str)
    x = range(len(labels))
    opt = df['optimal'].fillna(0).astype(int)
    inf = df['infeasible'].fillna(0).astype(int)
    pct = df['percent_optimal']

    fig, ax1 = plt.subplots(figsize=(max(8, len(labels) * 0.6), 6))

    width = 0.35
    ax1.bar([i - width/2 for i in x], opt, width, label='Optimal', color='#2ca02c')
    ax1.bar([i + width/2 for i in x], inf, width, label='Infeasible', color='#d62728')
    ax1.set_xlabel('dataset_subdir')
    ax1.set_ylabel('Counts')
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(x, pct, color='tab:blue', marker='o', label='Percent Optimal')
    ax2.set_ylabel('Percent Optimal (%)')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper right')

    plt.title('Optimal vs Infeasible per dataset subdir')
    plt.tight_layout()
    fig.savefig(out_img)
    print(f"Saved plot to {out_img}")


def main():
    parser = argparse.ArgumentParser(description="Aggregate results.log and plot summary by subdir")
    parser.add_argument('logfile', help='Path to results.log')
    parser.add_argument('--out-img', default='results_summary.png', help='Output PNG image')
    parser.add_argument('--out-csv', default=None, help='Optional CSV to save aggregated table')
    parser.add_argument('--show', action='store_true', help='Show the plot interactively (requires display)')
    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Log file {args.logfile} does not exist", file=sys.stderr)
        sys.exit(2)

    results = parse_log(args.logfile)
    if not results:
        print("No parsable results found in logfile. Exiting.")
        sys.exit(0)

    df = aggregate(results)

    out_df = df[['dataset_subdir', 'optimal', 'infeasible', 'percent_optimal']].copy()
    out_df['percent_optimal'] = out_df['percent_optimal'].apply(lambda v: (f"{v:.1f}" if not (isinstance(v, float) and math.isnan(v)) else 'NaN'))

    print('\nAggregated results:')
    print(out_df.to_string(index=False))
    if args.out_csv:
        df.to_csv(args.out_csv, index=False)
        print(f"Saved aggregated CSV to {args.out_csv}")

    plot_df(df, args.out_img)
    plt.savefig(args.out_img)


if __name__ == '__main__':
    main()
