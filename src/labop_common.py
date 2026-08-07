"""Shared constants/helpers describing this semester's labop survey and schedule layout.

Labop hours run 10 AM - 6 PM Mon-Thu and 10 AM - 5 PM Fri, giving 8+8+8+8+7 = 39
one-hour slots. With 39 students each doing exactly 2 hours and 2 labops needed
per slot, 39 students x 2 = 78 = 39 slots x 2 - the schedule is an exact match
when a feasible one exists.
"""

METADATA_COLUMNS = [
    "ID",
    "Start time",
    "Completion time",
    "Email",
    "Name",
    "Last modified time",
    "Last name",
    "First name",
]

EMAIL_COLUMN = "Email"

PREFERENCE_COLUMN = (
    "Do you prefer to have consecutive slots or slots spread across the week? "
    "(no guarantees though)"
)

MUST_HAVE = "MUST-HAVE"
UNAVAILABLE = "UNAVAILABLE"
AVAILABLE = "AVAILABLE"

# Ordered per-day slot counts for this semester's Mon-Fri layout.
DAY_SLOT_COUNTS = [8, 8, 8, 8, 7]
TOTAL_SLOTS = sum(DAY_SLOT_COUNTS)  # 39

SLOTS_PER_STUDENT = 2
STUDENTS_PER_SLOT = 2
# A student can only ever be assigned SLOTS_PER_STUDENT slots, so any more
# MUST-HAVEs than that can never be satisfied.
MAX_MUST_HAVE_PER_STUDENT = SLOTS_PER_STUDENT

HOUR_LABELS_MON_THU = [
    "10 AM - 11 AM",
    "11 AM - 12 PM",
    "12 PM - 1 PM",
    "1 PM - 2 PM",
    "2 PM - 3 PM",
    "3 PM - 4 PM",
    "4 PM - 5 PM",
    "5 PM - 6 PM",
]
HOUR_LABELS_FRI = HOUR_LABELS_MON_THU[:-1]
DAY_SUFFIXES = ["", "2", "3", "4", "5"]


def build_slot_columns():
    """Return the 39 slot column names in the same order the Forms export uses."""
    columns = []
    for day_index, suffix in enumerate(DAY_SUFFIXES):
        labels = HOUR_LABELS_FRI if day_index == len(DAY_SUFFIXES) - 1 else HOUR_LABELS_MON_THU
        columns.extend(f"{label}{suffix}" for label in labels)
    return columns


def get_slot_columns(df):
    """Slot columns are every column that isn't known metadata or the preference question."""
    excluded = set(METADATA_COLUMNS) | {PREFERENCE_COLUMN}
    return [c for c in df.columns if c not in excluded]


def get_slot_day_groups(slots):
    """Split an ordered slot list into per-day groups, for contiguity purposes.

    Falls back to a single group when the slot list doesn't match this semester's
    39-slot Mon-Fri layout (e.g. legacy/experimentation data with a different shape).
    """
    if len(slots) != TOTAL_SLOTS:
        return [slots]
    groups = []
    i = 0
    for count in DAY_SLOT_COUNTS:
        groups.append(slots[i : i + count])
        i += count
    return groups


def get_contiguous_pairs(slots):
    """Adjacent-slot pairs eligible for the 'contiguous' bonus, excluding day boundaries."""
    pairs = []
    for group in get_slot_day_groups(slots):
        for i in range(len(group) - 1):
            pairs.append((group[i], group[i + 1]))
    return pairs
