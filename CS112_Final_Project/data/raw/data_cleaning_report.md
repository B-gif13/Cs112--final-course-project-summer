# Data Cleaning & Validation Report — Week 1

**Project:** National Electricity Grid Network Analysis
**Task:** 1.1 Data Cleaning and Preprocessing (shared responsibility — all team members)
**Prepared by:** Aaron
**Date:** Week 1 submission

## 1. Datasets Reviewed

| Dataset | Rows | Columns | Source |
|---|---|---|---|
| utilities.csv | 10 | 4 | Benedicta's data-generation.ipynb (`random.seed(42)`) |
| substations.csv | 44 | 7 | Benedicta's data-generation.ipynb |
| lines.csv | 55 | 6 | Benedicta's data-generation.ipynb |

## 2. Validation Checks Performed

Ran `data_validation.py` against the generated CSVs to confirm the datasets are analysis-ready before EDA (Naeem) and network construction (Tayviah) proceed.

| Check | Result |
|---|---|
| Duplicate rows (exact) | 0 in all three files |
| Duplicate primary keys (substation_id, line_id, utility_id) | 0 |
| Lines referencing a non-existent substation ID | 0 |
| Substations referencing a non-existent utility ID | 0 |
| Self-loop lines (substation connected to itself) | 0 |
| Substation pairs connected by more than one line | **2 pairs** |
| Latitude/longitude outside West African bounds (4.5–11.5°N, -3.5–1.5°E) | 0 |
| Missing values (all columns, all 3 files) | 0 |
| Non-numeric values in numeric columns | 0 — capacity_mva, latitude, longitude, voltage_kv, length_km all typed correctly |

## 3. Findings

- **All referential integrity checks pass.** Every `from_substation`/`to_substation` in `lines.csv` maps to a real `substation_id`, and every `utility_id` in `substations.csv` maps to a real utility. No orphaned records.
- **No missing data and no duplicate records**, as expected from a seeded synthetic generator — but every check was still run explicitly rather than assumed, per the project guideline's instruction to treat this seriously even on clean data.
- **One genuine data-quality observation:** 2 substation pairs have more than one transmission/distribution line directly connecting them. This is plausible in a real grid (parallel circuits for redundancy) but is flagged here so Tayviah's NetworkX build treats it as a `MultiGraph` consideration rather than an unexplained anomaly — her script already uses `nx.MultiGraph()`, and separately collapses to a simple graph (keeping the shorter parallel line) for centrality metrics, so this is already handled correctly.
- **Value ranges are sane:** capacity 25–200 MVA, voltage levels restricted to the expected {11, 33, 69, 161, 330} kV, line lengths 2.1–79.9 km, status limited to "Active" / "Under Maintenance".

## 4. Imputation Strategy (documented per requirement, even though not needed)

No missing values were present in this run. Had any occurred, the team's agreed strategy would be:
- Categorical fields (region, status, type): flag as `"Unknown"` rather than dropping the row, to preserve network connectivity.
- Numeric fields (capacity_mva, length_km): impute using the median of the same voltage tier or region, not the global median, since capacity varies systematically by tier.
- Coordinates: never impute — a missing lat/long makes a substation unmappable, so such rows would be excluded from geographic visualizations only (not from network/EDA analysis).

## 5. Conclusion

The three datasets are clean, internally consistent, and ready for EDA and network analysis. No records were dropped or modified. The one flagged observation (parallel lines) is documented for the network-analysis and dashboard stages rather than treated as an error.
