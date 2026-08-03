"""
Data Validation Script - National Electricity Grid Network Analysis
Contributor: Aaron (Dashboard, Report & Presentation Lead)
Part of Task 1.1 (Data Cleaning and Preprocessing) - shared team responsibility

Runs structural validation checks on the three datasets produced by
Benedicta's data-generation.ipynb, ahead of EDA (Naeem) and network
analysis (Tayviah).
"""

import pandas as pd

utilities = pd.read_csv("../data/utilities.csv")
substations = pd.read_csv("../data/substations.csv")
lines = pd.read_csv("../data/lines.csv")

print("=== SHAPES ===")
print("utilities:", utilities.shape)
print("substations:", substations.shape)
print("lines:", lines.shape)

print("\n=== DUPLICATE RECORDS ===")
print("utilities duplicate rows:", utilities.duplicated().sum())
print("substations duplicate rows:", substations.duplicated().sum())
print("lines duplicate rows:", lines.duplicated().sum())
print("duplicate substation_id values:", substations["substation_id"].duplicated().sum())
print("duplicate line_id values:", lines["line_id"].duplicated().sum())
print("duplicate utility_id values:", utilities["utility_id"].duplicated().sum())

print("\n=== RELATIONSHIP / FOREIGN-KEY VALIDATION ===")
valid_subs = set(substations["substation_id"])
valid_utils = set(utilities["utility_id"])
orphan_from = lines[~lines["from_substation"].isin(valid_subs)]
orphan_to = lines[~lines["to_substation"].isin(valid_subs)]
orphan_util = substations[~substations["utility_id"].isin(valid_utils)]
print("Lines referencing a non-existent 'from_substation':", len(orphan_from))
print("Lines referencing a non-existent 'to_substation':", len(orphan_to))
print("Substations referencing a non-existent utility_id:", len(orphan_util))

print("\n=== SELF-LOOPS (a line connecting a substation to itself) ===")
self_loops = lines[lines["from_substation"] == lines["to_substation"]]
print("Self-loop lines found:", len(self_loops))

print("\n=== PARALLEL / DUPLICATE SUBSTATION-PAIR CONNECTIONS ===")
pairs = lines.apply(lambda r: tuple(sorted([r["from_substation"], r["to_substation"]])), axis=1)
dup_pairs = pairs[pairs.duplicated(keep=False)]
print("Substation pairs connected by more than one line:", pairs.duplicated().sum())
if len(dup_pairs) > 0:
    print(lines.loc[dup_pairs.index, ["line_id", "from_substation", "to_substation", "status"]])

print("\n=== GEOGRAPHIC BOUNDS CHECK (West Africa: lat 4.5-11.5, lon -3.5 to 1.5) ===")
bad_lat = substations[(substations["latitude"] < 4.5) | (substations["latitude"] > 11.5)]
bad_lon = substations[(substations["longitude"] < -3.5) | (substations["longitude"] > 1.5)]
print("Substations with out-of-bounds latitude:", len(bad_lat))
print("Substations with out-of-bounds longitude:", len(bad_lon))

print("\n=== DATA TYPE CHECK ===")
print(substations.dtypes)
print(lines.dtypes)

print("\n=== MISSING VALUES ===")
print("utilities:", utilities.isnull().sum().to_dict())
print("substations:", substations.isnull().sum().to_dict())
print("lines:", lines.isnull().sum().to_dict())

print("\n=== VALUE RANGE SANITY CHECKS ===")
print("capacity_mva range:", substations["capacity_mva"].min(), "-", substations["capacity_mva"].max())
print("voltage_kv unique values:", sorted(lines["voltage_kv"].unique()))
print("length_km range:", lines["length_km"].min(), "-", lines["length_km"].max())
print("line status values:", list(lines["status"].unique()))

print("\nValidation complete. See reports/data_cleaning_report.md for the write-up.")
