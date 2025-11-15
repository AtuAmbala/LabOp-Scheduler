import pandas as pd

df = pd.read_csv("responses.csv")
pref_cols = df.columns[8:]
violations = []
total_must = 0

for idx, row in df.iterrows():
    must_count = (row[pref_cols] == "MUST-HAVE").sum()
    unavailable_count = (row[pref_cols] == "UNAVAILABLE").sum()
    total_must += must_count
    if must_count > 3 or unavailable_count > 20:
        violations.append({
            "ID": row["ID"],
            "Name": row["Name"],
            "MUST-HAVE": must_count,
            "UNAVAILABLE": unavailable_count
        })
## if a slot has 3 MUST-HAVEs raise universal violation
## if a slot has less than 2 AVAILABLES raise universal violation
## for idx, col in df.itercols():

print("Total MUST-HAVE count:", total_must)

if violations:
    print("\nViolations found:")
    for v in violations:
        print(v)
else:
    print("\nNo violations detected.")
