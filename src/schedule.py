import os
import sys

import pandas as pd
import pulp as pl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from labop_common import (
    EMAIL_COLUMN,
    MUST_HAVE,
    SLOTS_PER_STUDENT,
    STUDENTS_PER_SLOT,
    UNAVAILABLE,
    get_contiguous_pairs,
    get_slot_columns,
)


def build_and_solve(df, mode=None, time_limit=60, msg=1):
    """Solve the labop assignment ILP for one term's responses.

    Each student is assigned exactly SLOTS_PER_STUDENT slots, each slot gets
    exactly STUDENTS_PER_SLOT students, subject to MUST-HAVE/UNAVAILABLE hard
    constraints. In CONTIGUOUS mode the objective rewards giving a student
    back-to-back slots within the same day.

    Returns (status, student_df, slot_df). student_df/slot_df are None unless
    status == "Optimal".
    """
    mode = mode or config.SCHEDULE_MODE
    students = df[EMAIL_COLUMN].astype(str).tolist()
    slots = get_slot_columns(df)

    preferences = {
        (s, t): str(df.loc[i, t]).strip().upper()
        for i, s in enumerate(students)
        for t in slots
    }

    model = pl.LpProblem("slot_assignment", pl.LpMinimize)

    assign = pl.LpVariable.dicts(
        "assign",
        [(s, t) for s in students for t in slots],
        0,
        1,
        pl.LpBinary,
    )

    for s in students:
        model += pl.lpSum(assign[(s, t)] for t in slots) == SLOTS_PER_STUDENT

    for t in slots:
        model += pl.lpSum(assign[(s, t)] for s in students) == STUDENTS_PER_SLOT

    for s in students:
        for t in slots:
            value = preferences[(s, t)]
            if MUST_HAVE in value:
                model += assign[(s, t)] == 1
            if UNAVAILABLE in value:
                model += assign[(s, t)] == 0

    if mode == "CONTIGUOUS":
        consec_vars = []
        for s in students:
            for i, (t1, t2) in enumerate(get_contiguous_pairs(slots)):
                y = pl.LpVariable(f"consec_{s}_{i}", 0, 1, pl.LpBinary)
                model += y <= assign[(s, t1)]
                model += y <= assign[(s, t2)]
                model += y >= assign[(s, t1)] + assign[(s, t2)] - 1
                consec_vars.append(y)
        model += -pl.lpSum(consec_vars)
    else:
        model += 0

    solver = pl.PULP_CBC_CMD(msg=msg, timeLimit=time_limit)
    model.solve(solver)
    status = pl.LpStatus[model.status]

    if status != "Optimal":
        return status, None, None

    student_info = {}
    for _, row in df.iterrows():
        email = str(row[EMAIL_COLUMN])
        student_info[email] = (
            row["ID"],
            row["Last name"],
            row["First name"],
        )

    slot_col_names = [f"slot {i + 1}" for i in range(SLOTS_PER_STUDENT)]
    rows_students = []
    for s in students:
        chosen = [t for t in slots if pl.value(assign[(s, t)]) > 0.5]
        chosen = chosen[:SLOTS_PER_STUDENT] + [""] * (SLOTS_PER_STUDENT - len(chosen))
        sid, lname, fname = student_info.get(s, ("", "", ""))
        rows_students.append([sid, s, lname, fname] + chosen)

    student_df = pd.DataFrame(
        rows_students,
        columns=[
            "student_id",
            "student_email",
            "student_last_name",
            "student_first_name",
        ]
        + slot_col_names,
    )

    student_col_names = [f"student {i + 1}" for i in range(STUDENTS_PER_SLOT)]
    rows_slots = []
    for t in slots:
        assigned_students = [s for s in students if pl.value(assign[(s, t)]) > 0.5]
        assigned_students = assigned_students[:STUDENTS_PER_SLOT] + [""] * (
            STUDENTS_PER_SLOT - len(assigned_students)
        )
        rows_slots.append([t] + assigned_students)

    slot_df = pd.DataFrame(rows_slots, columns=["slot"] + student_col_names)

    return status, student_df, slot_df


def main():
    input_path = os.path.join(os.getcwd(), sys.argv[1])
    output_path = os.path.join(os.getcwd(), sys.argv[2])

    df = pd.read_csv(input_path)
    status, student_df, slot_df = build_and_solve(df)

    if status != "Optimal":
        print("NO OPTIMAL ASSIGNMENT")
        return

    student_df.to_csv(output_path.replace(".csv", "_by_students.csv"), index=False)
    slot_df.to_csv(output_path.replace(".csv", "_by_slot.csv"), index=False)


if __name__ == "__main__":
    main()
