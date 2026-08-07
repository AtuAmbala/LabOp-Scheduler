# Fall 2026 experimentation

This semester's labop hours are 10 AM - 6 PM Mon-Thu and 10 AM - 5 PM Fri (39
one-hour slots), with exactly 39 students each doing exactly 2 hours and 2
labops required per slot (39 x 2 = 78 = 39 x 2 - an exact match). This folder
holds tooling to find where that exact match stops being achievable once
students report MUST-HAVE and UNAVAILABLE constraints.

Unlike `experimentation/spring-2026`, everything here imports the real
production solver from `src/schedule.py` (`build_and_solve`), so results
reflect the actual scheduler, not a separate re-implementation.

## Files

- `generate_sample_data.py` - generates a synthetic responses.csv in the real
  F26 column layout. `must_have` is the *total* number of MUST-HAVE entries
  across the whole 39-student dataset (each student gets at most one - this
  mirrors real usage, where most students submit zero and a handful submit
  exactly one). `unavailable` is an exact count applied to every student.
- `stress_test.py` - sweeps a grid of (must_have, unavailable), runs several
  random trials per cell through the production solver, and reports the
  feasibility rate (fraction that solved to `Optimal`).
- `test_scheduler.py` - pytest correctness checks: exactly-2 assignment,
  MUST-HAVE/UNAVAILABLE honored, an over-constrained case is correctly
  infeasible, contiguity math respects day boundaries, and the real
  `F26-TestSurveyData_39_Dummy.xlsx` example solves.
- `results/` - output CSVs/plots from `stress_test.py` runs.

Note: an earlier version of `generate_sample_data.py` applied `must_have` as
an exact per-student count to *every* student. That saturates almost
immediately - with 39 students spread over only 39 slots, even one MUST-HAVE
each collides onto some slot's 2-seat cap nearly every time (a birthday-paradox
effect), making `must_have=1` for everyone ~always infeasible regardless of
`unavailable`. The total-across-dataset framing here sweeps far more
informatively from "nobody cares" to "everybody insists on a slot."

## Usage

Generate one sample dataset:

```bash
python generate_sample_data.py --students 39 --must-have 10 --unavailable 20 --seed 0 --out /tmp/sample.csv
```

Run the feasibility sweep (defaults to a reasonable grid):

```bash
python stress_test.py \
    --must-have-values 0,5,10,15,20,25,30,35,39 \
    --unavailable-values 0,5,10,15,20,25,30,33,35,36 \
    --trials 8
```

This writes `results/feasibility_grid.csv` (one row per cell, with a
`feasibility_rate` column) and, if matplotlib is installed,
`results/feasibility_heatmap.png`.

Run the correctness tests:

```bash
pytest experimentation/fall-2026/test_scheduler.py
```

## Reading the results

`feasibility_rate` near 1.0 means that combination of MUST-HAVE volume and
per-student UNAVAILABLE count almost always produces a valid schedule; near
0.0 means it almost never does. Use the boundary between the two to inform
`src/check_responses.py`'s `MAX_UNAVAILABLE_PER_STUDENT_WARNING`, and to
decide whether the survey/process should cap how many students are allowed to
submit a MUST-HAVE at all (`MAX_MUST_HAVE_PER_STUDENT` is already hard-capped
at 2 per student for correctness reasons - that's not the interesting knob;
the *total number of students with any MUST-HAVE* is).

Caveats:
- MUST-HAVE and UNAVAILABLE slots are placed uniformly at random per student.
  Real students' unavailability tends to cluster (e.g. around a fixed class
  schedule) rather than scatter uniformly - real feasibility could differ from
  this model in either direction.
- Rates in the middle of the grid are noisy with a handful of trials (e.g. 15)
  - treat them as a ballpark, not a precise percentage. Increase `--trials`
    for a tighter estimate near a boundary you care about.
- The sweep doesn't vary class size (`--students`) or day-boundary effects;
  it's specifically about this semester's fixed 39-student/39-slot shape.

See the chat/report for a walkthrough of the actual sweep results.
