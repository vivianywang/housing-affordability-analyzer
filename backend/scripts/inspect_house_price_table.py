"""
Run this once from backend/scripts/:

    python inspect_house_price_table.py

It downloads the house price table one time and prints the real category
values for every dimension we're filtering on, so we can fix sources.py's
filters in one pass instead of one StatCan download per guess.
"""

from sources import _download_statcan_table, STATCAN_TABLES

df = _download_statcan_table(STATCAN_TABLES["house_price"])

print()
print("=== ALL COLUMNS ===")
for col in df.columns:
    print(f"  {col!r}")

dimensions_to_check = [
    "Statistics",
    "Age of primary household maintainer",
    "Presence of mortgage payments",
    "Number of bedrooms",
    "Condominium status",
]

for dimension in dimensions_to_check:
    matching_cols = [c for c in df.columns if dimension.lower() in c.lower() and "):" not in c]
    print()
    print(f"=== '{dimension}' ===")
    if not matching_cols:
        print("  (no matching row column found)")
        continue
    for col in matching_cols:
        print(f"  column: {col!r}")
        print(f"  unique values: {sorted(df[col].dropna().astype(str).unique().tolist())}")