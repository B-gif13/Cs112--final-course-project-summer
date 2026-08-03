import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

utilities = pd.read_csv("utilities.csv")
substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")

print("Loaded:", utilities.shape, substations.shape, lines.shape)

G = nx.MultiGraph()

for _, row in substations.iterrows():
    G.add_node(
        row["substation_id"],
        name=row["substation_name"],
        utility_id=row["utility_id"],
        region=row["region"],
        capacity_mva=row["capacity_mva"],
        latitude=row["latitude"],
        longitude=row["longitude"],
    )

for _, row in lines.iterrows():
    G.add_edge(
        row["from_substation"],
        row["to_substation"],
        line_id=row["line_id"],
        voltage_kv=row["voltage_kv"],
        length_km=row["length_km"],
        status=row["status"],
    )

print(f"\nGraph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

print("\n--- CONNECTIVITY ---")
print("Is connected:", nx.is_connected(G))

components = list(nx.connected_components(G))
print(f"Number of connected components: {len(components)}")
largest_cc = max(components, key=len)
print(f"Largest component size: {len(largest_cc)} / {G.number_of_nodes()} substations")

isolated = [n for n in components if len(n) == 1]
if isolated:
    isolated_ids = [list(c)[0] for c in isolated]
    print(f"Isolated substations (no lines at all): {isolated_ids}")

print(f"Graph density: {nx.density(G):.4f}")

print("\n--- DEGREE ANALYSIS ---")
degree_dict = dict(G.degree())
degree_df = pd.DataFrame(degree_dict.items(), columns=["substation_id", "degree"])
degree_df = degree_df.merge(
    substations[["substation_id", "substation_name", "region"]],
    on="substation_id", how="left"
).sort_values("degree", ascending=False)

print("Top 10 most-connected substations:")
print(degree_df.head(10).to_string(index=False))

avg_degree = sum(degree_dict.values()) / len(degree_dict)
print(f"\nAverage degree: {avg_degree:.2f}")

plt.figure(figsize=(8, 5))
plt.hist(degree_df["degree"], bins=range(0, degree_df["degree"].max() + 2), edgecolor="black")
plt.title("Substation Degree Distribution")
plt.xlabel("Degree (number of connected lines)")
plt.ylabel("Number of substations")
plt.tight_layout()
plt.savefig("degree_distribution.png")
plt.close()

print("\n--- CENTRALITY MEASURES ---")

SG = nx.Graph()
SG.add_nodes_from(G.nodes(data=True))
for u, v, data in G.edges(data=True):
    if SG.has_edge(u, v):
        if data["length_km"] < SG[u][v]["length_km"]:
            SG[u][v].update(data)
    else:
        SG.add_edge(u, v, **data)

degree_centrality = nx.degree_centrality(SG)
betweenness_centrality = nx.betweenness_centrality(SG, weight="length_km")
closeness_centrality = nx.closeness_centrality(SG, distance="length_km")

try:
    eigenvector_centrality = nx.eigenvector_centrality(SG, max_iter=1000)
except nx.PowerIterationFailedConvergence:
    eigenvector_centrality = {n: float("nan") for n in SG.nodes()}

centrality_df = pd.DataFrame({
    "substation_id": list(SG.nodes()),
    "degree_centrality": [degree_centrality[n] for n in SG.nodes()],
    "betweenness_centrality": [betweenness_centrality[n] for n in SG.nodes()],
    "closeness_centrality": [closeness_centrality[n] for n in SG.nodes()],
    "eigenvector_centrality": [eigenvector_centrality[n] for n in SG.nodes()],
})
centrality_df = centrality_df.merge(
    substations[["substation_id", "substation_name", "region"]],
    on="substation_id", how="left"
)

print("Top 5 by betweenness centrality:")
print(centrality_df.sort_values("betweenness_centrality", ascending=False)
      .head(5)[["substation_id", "substation_name", "betweenness_centrality"]]
      .to_string(index=False))

print("\nTop 5 by degree centrality:")
print(centrality_df.sort_values("degree_centrality", ascending=False)
      .head(5)[["substation_id", "substation_name", "degree_centrality"]]
      .to_string(index=False))

centrality_df.to_csv("substation_centrality.csv", index=False)
print("\nSaved -> substation_centrality.csv")

print("\n--- VULNERABILITY ANALYSIS ---")

bridges = list(nx.bridges(SG))
print(f"Bridges: {len(bridges)}")
for b in bridges:
    print(f"   {b[0]} -- {b[1]}")

cut_vertices = list(nx.articulation_points(SG))
print(f"\nArticulation points: {len(cut_vertices)}")
print(cut_vertices)

print("\n--- REGION-LEVEL SUMMARY ---")
region_summary = (
    centrality_df.groupby("region")
    .agg(
        num_substations=("substation_id", "count"),
        avg_betweenness=("betweenness_centrality", "mean"),
        avg_degree_centrality=("degree_centrality", "mean"),
    )
    .sort_values("avg_betweenness", ascending=False)
)
print(region_summary)

pos_geo = {n: (d["longitude"], d["latitude"]) for n, d in SG.nodes(data=True)}
node_sizes = [100 + 3000 * degree_centrality[n] for n in SG.nodes()]
node_colors = [betweenness_centrality[n] for n in SG.nodes()]

plt.figure(figsize=(10, 9))
nodes = nx.draw_networkx_nodes(SG, pos_geo, node_size=node_sizes, node_color=node_colors, cmap=plt.cm.viridis)
nx.draw_networkx_edges(SG, pos_geo, alpha=0.4, edge_color="gray")
nx.draw_networkx_labels(SG, pos_geo, font_size=6)
plt.colorbar(nodes, label="Betweenness centrality")
plt.title("Ghana National Grid Network (geographic layout)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("grid_network_geographic.png", dpi=150)
plt.close()

plt.figure(figsize=(10, 9))
pos_spring = nx.spring_layout(SG, seed=42, k=0.5)
region_list = sorted(substations["region"].unique())
region_color_map = {r: i for i, r in enumerate(region_list)}
node_colors_region = [region_color_map[SG.nodes[n]["region"]] for n in SG.nodes()]

nx.draw_networkx_nodes(SG, pos_spring, node_size=[100 + 3000 * degree_centrality[n] for n in SG.nodes()], node_color=node_colors_region, cmap=plt.cm.tab10)
nx.draw_networkx_edges(SG, pos_spring, alpha=0.4, edge_color="gray")
nx.draw_networkx_labels(SG, pos_spring, font_size=6)
plt.title("Ghana National Grid Network (spring layout)")
plt.axis("off")
plt.tight_layout()
plt.savefig("grid_network_spring.png", dpi=150)
plt.close()

print("\nSaved plots.")

print("\n--- SHORTEST PATH EXAMPLE ---")
sub_list = list(SG.nodes())
src, dst = sub_list[0], sub_list[-1]
if nx.has_path(SG, src, dst):
    path = nx.shortest_path(SG, src, dst, weight="length_km")
    dist = nx.shortest_path_length(SG, src, dst, weight="length_km")
    print(f"Shortest path {src} -> {dst}: {path}")
    print(f"Total length: {dist:.1f} km")
else:
    print(f"No path between {src} and {dst}")