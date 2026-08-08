

from __future__ import annotations

import math
from dataclasses import dataclass, field

import networkx as nx
import pandas as pd



def load_data(substations_path: str, lines_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    substations = pd.read_csv(substations_path)
    lines = pd.read_csv(lines_path)

    substations.columns = [c.strip() for c in substations.columns]
    lines.columns = [c.strip() for c in lines.columns]

    for col in ["substation_id", "substation_name", "utility_id", "region"]:
        if col in substations.columns:
            substations[col] = substations[col].astype(str).str.strip()

    for col in ["line_id", "from_substation", "to_substation", "status"]:
        if col in lines.columns:
            lines[col] = lines[col].astype(str).str.strip()

    for col in ["capacity_mva", "latitude", "longitude"]:
        if col in substations.columns:
            substations[col] = pd.to_numeric(substations[col], errors="coerce")

    for col in ["voltage_kv", "length_km"]:
        if col in lines.columns:
            lines[col] = pd.to_numeric(lines[col], errors="coerce")

    substations = substations.drop_duplicates(subset=["substation_id"]).reset_index(drop=True)
    lines = lines.drop_duplicates(subset=["line_id"]).reset_index(drop=True)

    valid_ids = set(substations["substation_id"])
    orphaned_mask = ~lines["from_substation"].isin(valid_ids) | ~lines["to_substation"].isin(valid_ids)
    orphaned = lines[orphaned_mask].copy()
    lines = lines[~orphaned_mask].reset_index(drop=True)

    
    self_loop_mask = lines["from_substation"] == lines["to_substation"]
    lines = lines[~self_loop_mask].reset_index(drop=True)

    substations.attrs["orphaned_lines"] = orphaned
    return substations, lines


def build_graph(substations: pd.DataFrame, lines: pd.DataFrame) -> nx.Graph:

    G = nx.Graph()

    for _, row in substations.iterrows():
        G.add_node(
            row["substation_id"],
            name=row.get("substation_name", row["substation_id"]),
            utility_id=row.get("utility_id"),
            region=row.get("region"),
            capacity_mva=row.get("capacity_mva"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
        )

    for _, row in lines.iterrows():
        u, v = row["from_substation"], row["to_substation"]
        if u not in G or v not in G:
            continue

        if G.has_edge(u, v):
            G[u][v]["parallel_lines"] = G[u][v].get("parallel_lines", 1) + 1
            G[u][v]["line_ids"].append(row["line_id"])
            continue
        G.add_edge(
            u,
            v,
            line_id=row["line_id"],
            line_ids=[row["line_id"]],
            voltage_kv=row.get("voltage_kv"),
            length_km=row.get("length_km"),
            status=row.get("status"),
            parallel_lines=1,
            weight=row.get("length_km") if pd.notna(row.get("length_km")) else 1.0,
        )

    return G


def compute_centrality(G: nx.Graph) -> pd.DataFrame:
 
    degree = dict(G.degree())
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)
    closeness = nx.closeness_centrality(G)
    clustering = nx.clustering(G)

    try:
        pagerank = nx.pagerank(G, weight="weight")
    except Exception:
        pagerank = {n: float("nan") for n in G.nodes()}

    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=1000, weight="weight")
    except (nx.PowerIterationFailedConvergence, nx.AmbiguousSolution, nx.NetworkXException):
        eigenvector = {n: float("nan") for n in G.nodes()}

    rows = []
    for n in G.nodes():
        data = G.nodes[n]
        rows.append({
            "substation_id": n,
            "name": data.get("name"),
            "region": data.get("region"),
            "capacity_mva": data.get("capacity_mva"),
            "degree": degree.get(n),
            "degree_centrality": degree_centrality.get(n),
            "betweenness_centrality": betweenness.get(n),
            "closeness_centrality": closeness.get(n),
            "eigenvector_centrality": eigenvector.get(n),
            "pagerank": pagerank.get(n),
            "clustering_coefficient": clustering.get(n),
        })

    df = pd.DataFrame(rows).set_index("substation_id")
    return df.sort_values("betweenness_centrality", ascending=False)



def network_summary(G: nx.Graph) -> dict:
  
    components = list(nx.connected_components(G))
    largest_cc = max(components, key=len) if components else set()
    Gc = G.subgraph(largest_cc).copy()

    summary = {
        "num_substations": G.number_of_nodes(),
        "num_lines": G.number_of_edges(),
        "density": nx.density(G),
        "num_connected_components": len(components),
        "largest_component_size": len(largest_cc),
        "isolated_substations": [n for n in G.nodes() if G.degree(n) == 0],
        "average_clustering": nx.average_clustering(G) if G.number_of_nodes() else float("nan"),
        "num_bridges": len(list(nx.bridges(G))),
    }

    if nx.is_connected(Gc) and Gc.number_of_nodes() > 1:
        summary["diameter_largest_component"] = nx.diameter(Gc)
        summary["avg_shortest_path_largest_component"] = nx.average_shortest_path_length(Gc)
    else:
        summary["diameter_largest_component"] = None
        summary["avg_shortest_path_largest_component"] = None

    return summary


def find_bridges(G: nx.Graph) -> list[tuple[str, str]]:

    return list(nx.bridges(G))


def detect_communities(G: nx.Graph) -> dict[str, int]:
    
    try:
        communities = nx.community.greedy_modularity_communities(G, weight="weight")
    except Exception:
        return {n: 0 for n in G.nodes()}
    mapping = {}
    for cid, group in enumerate(communities):
        for n in group:
            mapping[n] = cid
    return mapping


def rank_critical_substations(centrality_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    
    metrics = ["degree_centrality", "betweenness_centrality", "closeness_centrality", "pagerank"]
    norm = centrality_df[metrics].copy()
    for m in metrics:
        col = norm[m]
        rng = col.max() - col.min()
        norm[m] = (col - col.min()) / rng if rng > 0 else 0.0
    composite = norm.mean(axis=1)
    out = centrality_df.copy()
    out["composite_criticality_score"] = composite
    return out.sort_values("composite_criticality_score", ascending=False).head(top_n)



@dataclass
class ContingencyResult:
    removed_node: str
    removed_name: str
    components_before: int
    components_after: int
    largest_cc_before: int
    largest_cc_after: int
    newly_isolated: list = field(default_factory=list)
    fragments_network: bool = False
    substations_cut_off: int = 0

    def as_dict(self) -> dict:
        return {
            "substation_id": self.removed_node,
            "name": self.removed_name,
            "components_before": self.components_before,
            "components_after": self.components_after,
            "largest_cc_before": self.largest_cc_before,
            "largest_cc_after": self.largest_cc_after,
            "substations_cut_off": self.substations_cut_off,
            "fragments_network": self.fragments_network,
            "newly_isolated": ", ".join(self.newly_isolated) if self.newly_isolated else "",
        }


def n1_contingency_single(G: nx.Graph, node: str) -> ContingencyResult:
   
    if node not in G:
        raise KeyError(f"Substation '{node}' not found in graph")

    components_before = nx.number_connected_components(G)
    largest_before = len(max(nx.connected_components(G), key=len))

    G_minus = G.copy()
    name = G.nodes[node].get("name", node)
    neighbors_before = set(G.neighbors(node))
    G_minus.remove_node(node)

    components_after = nx.number_connected_components(G_minus)
    largest_after = len(max(nx.connected_components(G_minus), key=len)) if G_minus.number_of_nodes() else 0


    remaining_components = list(nx.connected_components(G_minus))
    newly_isolated = [c.pop() for c in remaining_components if len(c) == 1] if remaining_components else []
  
    substations_cut_off = sum(len(c) for c in remaining_components if len(c) < largest_after) if remaining_components else 0

    fragments = components_after > components_before

    return ContingencyResult(
        removed_node=node,
        removed_name=name,
        components_before=components_before,
        components_after=components_after,
        largest_cc_before=largest_before,
        largest_cc_after=largest_after,
        newly_isolated=newly_isolated,
        fragments_network=fragments,
        substations_cut_off=substations_cut_off,
    )


def n1_contingency_full(G: nx.Graph) -> pd.DataFrame:

    results = [n1_contingency_single(G, n).as_dict() for n in G.nodes()]
    df = pd.DataFrame(results)
    df["largest_cc_drop"] = df["largest_cc_before"] - df["largest_cc_after"]
    df = df.sort_values(
        ["fragments_network", "largest_cc_drop", "components_after"],
        ascending=[False, False, False],
    )
    return df.set_index("substation_id")


def n1_line_contingency_full(G: nx.Graph) -> pd.DataFrame:

    components_before = nx.number_connected_components(G)
    rows = []
    for u, v, data in G.edges(data=True):
        Gm = G.copy()
        Gm.remove_edge(u, v)
        components_after = nx.number_connected_components(Gm)
        rows.append({
            "line_id": data.get("line_id"),
            "from_substation": u,
            "to_substation": v,
            "voltage_kv": data.get("voltage_kv"),
            "components_before": components_before,
            "components_after": components_after,
            "is_bridge": components_after > components_before,
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["is_bridge", "components_after"], ascending=[False, False])




def run_full_analysis(substations_path: str, lines_path: str) -> dict:
    substations, lines = load_data(substations_path, lines_path)
    G = build_graph(substations, lines)
    centrality_df = compute_centrality(G)
    return {
        "graph": G,
        "substations": substations,
        "lines": lines,
        "centrality": centrality_df,
        "summary": network_summary(G),
        "bridges": find_bridges(G),
        "critical": rank_critical_substations(centrality_df, top_n=10),
    }


if __name__ == "__main__":
    results = run_full_analysis("substations.csv", "lines.csv")
    print("=== Network summary ===")
    for k, v in results["summary"].items():
        print(f"{k}: {v}")
    print("\n=== Top 10 critical substations (composite score) ===")
    print(results["critical"][["name", "region", "composite_criticality_score"]])
    print(f"\n=== Bridges (single lines that would fragment the network) ===")
    print(results["bridges"])
    print("\n=== N-1 substation contingency (top 10 most disruptive) ===")
    print(n1_contingency_full(results["graph"]).head(10))
