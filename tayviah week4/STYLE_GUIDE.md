# Visualization Style Guide — National Grid Network Analysis (Task 3.2)

## Palette
| Purpose | Color | Hex |
|---|---|---|
| Canvas / background | Slate 900 | `#0F172A` |
| Primary text | Slate 200 | `#E2E8F0` |
| Gridlines / borders | Slate 700 | `#334155` |
| Active line status | Green | `#22C55E` |
| Under Maintenance status | Amber | `#F59E0B` |
| Region categories | Matplotlib `tab10` / Plotly `Set3` (qualitative, colorblind-considerate) |
| Sequential scales (centrality, year) | Viridis |
| Density scales (heatmaps) | Magma / YlOrRd |

Rationale: dark canvas reads well for network graphs (edges/nodes pop), and
Viridis/Magma are perceptually uniform and colorblind-safe for anything
implying magnitude (centrality, density, flow).

## Typography
- Font family: `Georgia, 'Times New Roman', serif` — matches a "publication"
  / report feel rather than a dashboard feel.
- Titles: 12–14pt, one-line subtitle explaining what size/color encode.
- Node/edge labels: 6–8pt to avoid clutter on graphs with 40+ nodes.

## Encoding conventions (used consistently across all charts)
- **Node size** → degree centrality (bigger = more direct connections)
- **Node/edge color (sequential)** → betweenness centrality or commissioning year
- **Node color (categorical)** → region
- **Edge color** → line status (green = Active, amber = Under Maintenance)
- **Arc/edge width** (chord diagram) → number of connecting lines

## File types
- Static "publication" figures → PNG, 220dpi, `bbox_inches="tight"`, saved via `savefig` (never `plt.show()` in scripts — see earlier note on headless environments).
- Interactive figures (3D network, animated map) → standalone HTML via Plotly (`include_plotlyjs="cdn"`) so they can be opened directly in a browser or embedded in the dashboard without a Python runtime.

## Known limitation / data gap
`commissioning_year` is **not present** in the source data (`datagen.py`
only produces `capacity_mva`, `latitude`, `longitude` for substations — no
year field, and no year field on lines either). The animated expansion map
uses a synthetic seeded random year (1985–2023) as a placeholder. Before
finalizing the report, ask Benedicta to add a real `commissioning_year`
column and rerun `advanced_visualizations.py` — no other code changes needed.
