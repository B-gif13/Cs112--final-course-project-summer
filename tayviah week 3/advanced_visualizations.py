
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
import plotly.graph_objects as go
import plotly.express as px

COLOR_BG = "#0F172A"        # slate-900, dark canvas for publication figures
COLOR_TEXT = "#E2E8F0"      # slate-200
COLOR_GRID = "#334155"      # slate-700
REGION_PALETTE = px.colors.qualitative.Set3
FONT_FAMILY = "Georgia, 'Times New Roman', serif"
STATUS_COLORS = {"Active": "#22C55E", "Under Maintenance": "#F59E0B"}

plt.rcParams.update({
    "font.family": "serif",
    "figure.facecolor": COLOR_BG,
    "axes.facecolor": COLOR_BG,
    "axes.edgecolor": COLOR_GRID,
    "axes.labelcolor": COLOR_TEXT,
    "text.color": COLOR_TEXT,
    "xtick.color": COLOR_TEXT,
    "ytick.color": COLOR_TEXT,
    "axes.titlecolor": COLOR_TEXT,
    "savefig.facecolor": COLOR_BG,
})

utilities = pd.read_csv("utilities.csv")
substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")

rng = np.random.default_rng(42)
substations["commissioning_year"] = rng.integers(1985, 2024, size=len(substations))

G = nx.Graph()
for _, row in substations.iterrows():
    G.add_node(row["substation_id"], **row.to_dict())
for _, row in lines.iterrows():
    u, v = row["from_substation"], row["to_substation"]
    if G.has_edge(u, v):
        continue
    G.add_edge(u, v, **row.to_dict())

degree_centrality = nx.degree_centrality(G)
betweenness_centrality = nx.betweenness_centrality(G, weight="length_km")

fig, ax = plt.subplots(figsize=(12, 10))
pos = nx.spring_layout(G, seed=42, k=0.6, iterations=100)

region_list = sorted(substations["region"].unique())
region_cmap = plt.get_cmap("tab10", len(region_list))
region_color = {r: region_cmap(i) for i, r in enumerate(region_list)}
node_colors = [region_color[G.nodes[n]["region"]] for n in G.nodes()]
node_sizes = [300 + 4000 * degree_centrality[n] for n in G.nodes()]

edge_status = [G[u][v]["status"] for u, v in G.edges()]
edge_colors = [STATUS_COLORS.get(s, "#94A3B8") for s in edge_status]

nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=1.4, alpha=0.65)
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,
                        edgecolors="white", linewidths=0.6)
nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_color="white")

legend_handles = [mpatches.Patch(color=region_color[r], label=r) for r in region_list]
status_handles = [mpatches.Patch(color=c, label=s) for s, c in STATUS_COLORS.items()]
leg1 = ax.legend(handles=legend_handles, title="Region", loc="upper left",
                  bbox_to_anchor=(1.01, 1), fontsize=8, title_fontsize=9)
ax.add_artist(leg1)
ax.legend(handles=status_handles, title="Line status", loc="lower left",
          bbox_to_anchor=(1.01, 0), fontsize=8, title_fontsize=9)

ax.set_title("Ghana National Grid — Substation Network\n"
              "Node size = degree centrality  |  Node color = region  |  Edge color = line status",
              fontsize=13, pad=16)
ax.axis("off")
plt.tight_layout()
plt.savefig("network_force_directed_pub.png", dpi=220, bbox_inches="tight")
plt.close()
print("Saved: network_force_directed_pub.png")

pos3d = nx.spring_layout(G, seed=42, dim=3, k=0.6, iterations=100)

edge_x, edge_y, edge_z = [], [], []
for u, v in G.edges():
    x0, y0, z0 = pos3d[u]
    x1, y1, z1 = pos3d[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]
    edge_z += [z0, z1, None]

edge_trace = go.Scatter3d(
    x=edge_x, y=edge_y, z=edge_z, mode="lines",
    line=dict(color="rgba(150,150,150,0.4)", width=2), hoverinfo="none"
)

node_x = [pos3d[n][0] for n in G.nodes()]
node_y = [pos3d[n][1] for n in G.nodes()]
node_z = [pos3d[n][2] for n in G.nodes()]
node_text = [
    f"{n} ({G.nodes[n]['substation_name']})<br>Region: {G.nodes[n]['region']}<br>"
    f"Capacity: {G.nodes[n]['capacity_mva']} MVA<br>Degree centrality: {degree_centrality[n]:.3f}"
    for n in G.nodes()
]
node_trace = go.Scatter3d(
    x=node_x, y=node_y, z=node_z, mode="markers+text",
    text=[n for n in G.nodes()], textposition="top center", textfont=dict(size=8, color="white"),
    hovertext=node_text, hoverinfo="text",
    marker=dict(
        size=[8 + 40 * degree_centrality[n] for n in G.nodes()],
        color=[betweenness_centrality[n] for n in G.nodes()],
        colorscale="Viridis", colorbar=dict(title="Betweenness"),
        line=dict(color="white", width=0.5),
    )
)

fig3d = go.Figure(data=[edge_trace, node_trace])
fig3d.update_layout(
    title="Ghana National Grid — Interactive 3D Network",
    showlegend=False,
    scene=dict(
        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
        bgcolor=COLOR_BG,
    ),
    paper_bgcolor=COLOR_BG, font=dict(color=COLOR_TEXT, family=FONT_FAMILY),
    margin=dict(l=0, r=0, t=50, b=0),
)
fig3d.write_html("network_3d.html", include_plotlyjs="cdn")
print("Saved: network_3d.html")


sub_region = substations.set_index("substation_id")["region"]
lines2 = lines.copy()
lines2["from_region"] = lines2["from_substation"].map(sub_region)
lines2["to_region"] = lines2["to_substation"].map(sub_region)

flow = (
    lines2.groupby(["from_region", "to_region"]).size()
    .reset_index(name="count")
)
flow_matrix = pd.DataFrame(0, index=region_list, columns=region_list)
for _, r in flow.iterrows():
    a, b = r["from_region"], r["to_region"]
    if a == b:
        continue
    flow_matrix.loc[a, b] += r["count"]
    flow_matrix.loc[b, a] += r["count"]

n = len(region_list)
angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
radius = 1.0
node_xy = {region_list[i]: (radius * np.cos(angles[i]), radius * np.sin(angles[i])) for i in range(n)}

fig, ax = plt.subplots(figsize=(11, 11))
max_flow = flow_matrix.values.max() if flow_matrix.values.max() > 0 else 1

for i in range(n):
    for j in range(i + 1, n):
        w = flow_matrix.iloc[i, j]
        if w == 0:
            continue
        p0 = node_xy[region_list[i]]
        p2 = node_xy[region_list[j]]
        verts = [p0, (0, 0), p2]
        codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
        path = Path(verts, codes)
        patch = mpatches.PathPatch(
            path, facecolor="none", lw=0.5 + 4 * (w / max_flow),
            edgecolor=region_cmap(i), alpha=0.5
        )
        ax.add_patch(patch)

for i, r in enumerate(region_list):
    x, y = node_xy[r]
    ax.scatter([x], [y], s=600, color=region_cmap(i), zorder=5, edgecolors="white")
    ax.text(x * 1.18, y * 1.18, r, ha="center", va="center", fontsize=10, color="white")

ax.set_xlim(-1.6, 1.6)
ax.set_ylim(-1.6, 1.6)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Inter-Regional Power Line Flows\nArc width = number of connecting lines between regions",
             fontsize=13, pad=10)
plt.tight_layout()
plt.savefig("chord_diagram_regions.png", dpi=220, bbox_inches="tight")
plt.close()
print("Saved: chord_diagram_regions.png")


fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(flow_matrix.values, cmap="magma")
ax.set_xticks(range(n)); ax.set_xticklabels(region_list, rotation=45, ha="right")
ax.set_yticks(range(n)); ax.set_yticklabels(region_list)
for i in range(n):
    for j in range(n):
        v = flow_matrix.iloc[i, j]
        if v > 0:
            ax.text(j, i, int(v), ha="center", va="center",
                     color="white" if v < max_flow * 0.6 else "black", fontsize=8)
fig.colorbar(im, ax=ax, label="Number of lines between regions")
ax.set_title("Inter-Regional Line Density Heatmap", fontsize=13, pad=12)
plt.tight_layout()
plt.savefig("heatmap_line_density.png", dpi=220, bbox_inches="tight")
plt.close()
print("Saved: heatmap_line_density.png")


lines2["from_region"] = lines2["from_substation"].map(sub_region)
status_by_region = pd.crosstab(lines2["from_region"], lines2["status"])
status_by_region = status_by_region.reindex(region_list, fill_value=0)

fig, ax = plt.subplots(figsize=(6, 8))
im = ax.imshow(status_by_region.values, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(len(status_by_region.columns))); ax.set_xticklabels(status_by_region.columns, rotation=20, ha="right")
ax.set_yticks(range(len(region_list))); ax.set_yticklabels(region_list)
for i in range(len(region_list)):
    for j in range(len(status_by_region.columns)):
        v = status_by_region.values[i, j]
        ax.text(j, i, int(v), ha="center", va="center", fontsize=8,
                 color="white" if v < status_by_region.values.max() * 0.6 else "black")
fig.colorbar(im, ax=ax, label="Number of lines")
ax.set_title("Line Status Concentration by Region\n(origin substation region)", fontsize=12, pad=12)
plt.tight_layout()
plt.savefig("heatmap_maintenance_status.png", dpi=220, bbox_inches="tight")
plt.close()
print("Saved: heatmap_maintenance_status.png")


util_sub = substations.merge(utilities[["utility_id", "utility_name"]], on="utility_id", how="left")
footprint = util_sub.groupby("utility_name").agg(
    num_substations=("substation_id", "count"),
    total_capacity_mva=("capacity_mva", "sum"),
).reset_index().sort_values("total_capacity_mva", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

axes[0].barh(footprint["utility_name"], footprint["num_substations"], color="#38BDF8")
axes[0].set_title("Number of Substations per Utility")
axes[0].set_xlabel("Substations")
axes[0].invert_yaxis()

axes[1].barh(footprint["utility_name"], footprint["total_capacity_mva"], color="#A78BFA")
axes[1].set_title("Total Installed Capacity per Utility (MVA)")
axes[1].set_xlabel("Capacity (MVA)")
axes[1].invert_yaxis()

fig.suptitle("Utility Infrastructure Footprint Comparison", fontsize=14)
plt.tight_layout()
plt.savefig("utility_footprint_comparison.png", dpi=220, bbox_inches="tight")
plt.close()
print("Saved: utility_footprint_comparison.png")


years = sorted(substations["commissioning_year"].unique())
frame_years = list(range(min(years), max(years) + 1))

frames = []
for y in frame_years:
    active = substations[substations["commissioning_year"] <= y]
    frames.append(go.Frame(
        name=str(y),
        data=[go.Scattergeo(
            lat=active["latitude"], lon=active["longitude"],
            text=active["substation_name"],
            mode="markers",
            marker=dict(size=9, color=active["commissioning_year"],
                        colorscale="Viridis", cmin=min(years), cmax=max(years),
                        line=dict(width=0.5, color="white")),
        )]
    ))

first = substations[substations["commissioning_year"] <= frame_years[0]]
fig_anim = go.Figure(
    data=[go.Scattergeo(
        lat=first["latitude"], lon=first["longitude"], text=first["substation_name"],
        mode="markers",
        marker=dict(size=9, color=first["commissioning_year"], colorscale="Viridis",
                    cmin=min(years), cmax=max(years), line=dict(width=0.5, color="white")),
    )],
    frames=frames,
)
fig_anim.update_geos(
    scope="africa", center=dict(lat=7.9, lon=-1.0), projection_scale=6,
    showcountries=True, showland=True, landcolor="#1E293B", bgcolor=COLOR_BG,
)
fig_anim.update_layout(
    title="Grid Expansion by Commissioning Year (synthetic data — replace with real field)",
    paper_bgcolor=COLOR_BG, font=dict(color=COLOR_TEXT, family=FONT_FAMILY),
    updatemenus=[dict(
        type="buttons", showactive=False,
        buttons=[dict(label="Play", method="animate",
                       args=[None, {"frame": {"duration": 250, "redraw": True}, "fromcurrent": True}]),
                 dict(label="Pause", method="animate",
                       args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])],
    )],
    sliders=[dict(steps=[
        dict(method="animate", args=[[str(y)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
             label=str(y)) for y in frame_years
    ])],
)
fig_anim.write_html("grid_expansion_animated.html", include_plotlyjs="cdn")
print("Saved: grid_expansion_animated.html")

showcase_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>National Grid Network — Visualization Showcase</title>
<style>
  body {{ background:{COLOR_BG}; color:{COLOR_TEXT}; font-family:{FONT_FAMILY}; margin:0; padding:40px; }}
  h1 {{ font-size:2rem; border-bottom:2px solid {COLOR_GRID}; padding-bottom:12px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:32px; margin-top:32px; }}
  .card {{ background:#1E293B; border-radius:10px; padding:20px; }}
  .card img {{ width:100%; border-radius:6px; }}
  .card h3 {{ margin-top:0; }}
  a {{ color:#38BDF8; }}
  .full {{ grid-column: 1 / -1; }}
</style>
</head>
<body>
<h1>National Electricity Grid — Visualization Showcase</h1>
<p>Team 3 (Tayviah) — Network graph, centrality, and grid-flow visualizations.</p>
<div class="grid">
  <div class="card"><h3>Force-Directed Network</h3><img src="network_force_directed_pub.png"></div>
  <div class="card"><h3>Utility Infrastructure Footprint</h3><img src="utility_footprint_comparison.png"></div>
  <div class="card"><h3>Inter-Regional Chord Diagram</h3><img src="chord_diagram_regions.png"></div>
  <div class="card"><h3>Region x Region Line Density</h3><img src="heatmap_line_density.png"></div>
  <div class="card"><h3>Maintenance Status by Region</h3><img src="heatmap_maintenance_status.png"></div>
  <div class="card full"><h3>Interactive 3D Network</h3><p><a href="network_3d.html">Open interactive 3D view →</a></p></div>
  <div class="card full"><h3>Animated Grid Expansion</h3><p><a href="grid_expansion_animated.html">Open animated map →</a> (synthetic commissioning years — pending real data)</p></div>
</div>
</body>
</html>"""
with open("visualization_showcase.html", "w") as f:
    f.write(showcase_html)
print("Saved: visualization_showcase.html")

print("\nAll Task 3.2 deliverables generated.")
