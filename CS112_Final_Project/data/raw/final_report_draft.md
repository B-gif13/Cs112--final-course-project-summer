# National Electricity Grid Network Analysis — Final Report (Draft)

**Team:** Benedicta (Data Lead) · Naeem (EDA Lead) · Tayviah (Network Analysis Lead) · Aaron (Dashboard, Report & Presentation Lead)

> Status: Week 1 draft. Sections below are outlined with placeholders; Week 1
> content is filled in now, later sections will be completed as each lead's
> analysis finalizes.

## 1. Dataset Description and Cleaning Steps ✅ (Week 1 — complete)

- 3 CSVs generated via seeded script (`random.seed(42)`): 10 utilities, 44 substations, 55 lines.
- Full validation run (see `reports/data_cleaning_report.md`): no missing values, no duplicate records, no orphaned foreign keys, no out-of-bounds coordinates.
- One flagged observation: 2 substation pairs carry more than one direct line — handled as a MultiGraph consideration in the network build.

## 2. Key Findings from EDA (Naeem) — *pending Naeem's write-up*

- [ ] Utility type distribution
- [ ] Substations by region
- [ ] Capacity distribution and top/bottom regions by total capacity
- [ ] Voltage-level distribution
- [ ] Line status (Active vs Under Maintenance) breakdown
- [ ] Top 10 most-connected substations

## 3. Insights from Merged/Integrated Data — *pending*

## 4. Network Analysis Results (Tayviah) — *in progress, initial results available*

- Graph built: substations as nodes, lines as edges (MultiGraph collapsed to simple graph for centrality).
- Degree, betweenness, closeness, eigenvector centrality calculated — see `data/substation_centrality.csv`.
- Bridges and articulation points identified for vulnerability analysis.
- [ ] N-1 contingency check — remove top hub, measure connected-component change
- [ ] Region-level centrality summary interpretation

## 5. Challenges Faced and Solutions Applied — *ongoing, update weekly*

- Week 1: none blocking; validation confirmed data is analysis-ready.

## 6. Limitations and Caveats

- All figures (coordinates, capacities, connections) are synthetic/illustrative — not real Ghanaian grid data.
- Betweenness/degree centrality are structural proxies, not measures of real electrical load, voltage stability, or protection behavior.
- N-1 contingency here is a simplified graph-based approximation, not a full power-flow or security-constrained contingency study.

## 7. References

- Project dataset generator (seeded, `random.seed(42)`)
- NetworkX documentation
