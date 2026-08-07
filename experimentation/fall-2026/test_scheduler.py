"""Correctness tests for the production solver (src/schedule.py) against this
semester's exactly-2-slots-per-student, 39-slot constraints.

Run with: pytest experimentation/fall-2026/test_scheduler.py
"""
import os
import sys

import pandas as pd
import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, THIS_DIR)

from schedule import build_and_solve  # noqa: E402
from labop_common import (  # noqa: E402
    SLOTS_PER_STUDENT,
    STUDENTS_PER_SLOT,
    build_slot_columns,
    get_contiguous_pairs,
    get_slot_columns,
)
from generate_sample_data import generate_dataframe  # noqa: E402

STUDENT_SLOT_COLS = [f"slot {i + 1}" for i in range(SLOTS_PER_STUDENT)]
SLOT_STUDENT_COLS = [f"student {i + 1}" for i in range(STUDENTS_PER_SLOT)]


def test_easy_case_is_feasible_and_balanced():
    df = generate_dataframe(num_students=39, must_have=0, unavailable=10, seed=1)
    status, student_df, slot_df = build_and_solve(df, mode="SPREAD", time_limit=30, msg=0)
    assert status == "Optimal"

    for _, row in student_df.iterrows():
        chosen = [row[c] for c in STUDENT_SLOT_COLS]
        assert all(c != "" for c in chosen), "every student should get exactly 2 slots"
        assert len(set(chosen)) == SLOTS_PER_STUDENT, "a student's 2 slots must be distinct"

    for _, row in slot_df.iterrows():
        chosen = [row[c] for c in SLOT_STUDENT_COLS]
        assert all(c != "" for c in chosen), "every slot should get exactly 2 students"
        assert len(set(chosen)) == STUDENTS_PER_SLOT


def test_must_have_is_honored():
    # Note: applying a MUST-HAVE to every one of the 39 students at once (as
    # generate_dataframe's `must_have` count does) collides often enough on
    # shared slots to make the whole model infeasible - see
    # experimentation/fall-2026/README.md. That's a real feasibility finding,
    # not a bug, so this test isolates the MUST-HAVE mechanism itself instead:
    # it takes a slot from an already-solved feasible baseline and promotes it
    # to a hard MUST-HAVE for one student, which is guaranteed to stay
    # feasible (that baseline solution already satisfies it).
    df = generate_dataframe(num_students=39, must_have=0, unavailable=10, seed=1)
    status, student_df, _ = build_and_solve(df, mode="SPREAD", time_limit=30, msg=0)
    assert status == "Optimal"

    target_email = df.iloc[0]["Email"]
    baseline = student_df.set_index("student_email")
    promoted_slot = baseline.loc[target_email, STUDENT_SLOT_COLS[0]]

    df.loc[0, promoted_slot] = "MUST-HAVE"
    status2, student_df2, _ = build_and_solve(df, mode="SPREAD", time_limit=30, msg=0)
    assert status2 == "Optimal"
    assigned2 = {student_df2.set_index("student_email").loc[target_email, c] for c in STUDENT_SLOT_COLS}
    assert promoted_slot in assigned2


def test_unavailable_is_honored():
    # Same reasoning as test_must_have_is_honored: derive the mutation from an
    # already-solved feasible baseline so the test is deterministic rather
    # than dependent on a random full-population UNAVAILABLE count staying
    # feasible.
    df = generate_dataframe(num_students=39, must_have=0, unavailable=10, seed=1)
    status, student_df, _ = build_and_solve(df, mode="SPREAD", time_limit=30, msg=0)
    assert status == "Optimal"

    slots = get_slot_columns(df)
    target_email = df.iloc[0]["Email"]
    baseline_assigned = set(student_df.set_index("student_email").loc[target_email, STUDENT_SLOT_COLS])
    unassigned_slot = next(t for t in slots if t not in baseline_assigned and df.loc[0, t] == "AVAILABLE")

    df.loc[0, unassigned_slot] = "UNAVAILABLE"
    status2, student_df2, _ = build_and_solve(df, mode="SPREAD", time_limit=30, msg=0)
    assert status2 == "Optimal"
    assigned2 = {student_df2.set_index("student_email").loc[target_email, c] for c in STUDENT_SLOT_COLS}
    assert unassigned_slot not in assigned2


def test_three_must_haves_is_infeasible():
    # A student can only ever hold 2 slots, so a 3rd MUST-HAVE can never be
    # satisfied - this should make the whole model infeasible.
    df = generate_dataframe(num_students=39, must_have=0, unavailable=10, seed=4)
    slots = get_slot_columns(df)
    df.loc[0, slots[0]] = "MUST-HAVE"
    df.loc[0, slots[1]] = "MUST-HAVE"
    df.loc[0, slots[2]] = "MUST-HAVE"
    status, student_df, slot_df = build_and_solve(df, mode="SPREAD", time_limit=30, msg=0)
    assert status != "Optimal"
    assert student_df is None
    assert slot_df is None


def test_contiguous_pairs_respect_day_boundaries():
    slots = build_slot_columns()
    pairs = get_contiguous_pairs(slots)
    # Monday's last slot and Tuesday's first slot are adjacent columns but not
    # adjacent in time - they must not be treated as a contiguous pair.
    assert ("5 PM - 6 PM", "10 AM - 11 AM2") not in pairs
    # within-day adjacent slots should be
    assert ("10 AM - 11 AM", "11 AM - 12 PM") in pairs
    # Friday only runs to 5 PM, so "4 PM - 5 PM5" should have no successor
    assert not any(t1 == "4 PM - 5 PM5" for t1, _ in pairs)


def test_real_example_survey_is_feasible():
    excel_path = os.path.join(REPO_ROOT, "F26-TestSurveyData_39_Dummy.xlsx")
    if not os.path.exists(excel_path):
        pytest.skip("F26-TestSurveyData_39_Dummy.xlsx not present in repo root")
    pd_excel = pytest.importorskip("openpyxl")  # noqa: F841  (ensures a clear skip if missing)
    df = pd.read_excel(excel_path)
    status, student_df, slot_df = build_and_solve(df, mode="SPREAD", time_limit=60, msg=0)
    assert status == "Optimal"
    assert len(student_df) == len(df)
    assert len(slot_df) == len(build_slot_columns())
