

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

import network_analysis as na

APP_TITLE = "GridCare Network Analyzer — Centrality & N-1 Contingency"
DEFAULT_SUBSTATIONS = "substations.csv"
DEFAULT_LINES = "lines.csv"


class GridNetworkApp(tk.Tk):
    def __init__(self, substations_path=DEFAULT_SUBSTATIONS, lines_path=DEFAULT_LINES):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.substations_path = substations_path
        self.lines_path = lines_path
        self.G: nx.Graph | None = None
        self.centrality_df = None
        self.layout_pos = None

        self._build_menu()
        self._build_layout()

        self.status_var = tk.StringVar(value="Loading data...")
        ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken").pack(
            side="bottom", fill="x"
        )

        self.after(50, self.load_data)

   
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open substations.csv...", command=self.pick_substations)
        file_menu.add_command(label="Open lines.csv...", command=self.pick_lines)
        file_menu.add_command(label="Reload", command=self.load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def pick_substations(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.substations_path = path
            self.load_data()

    def pick_lines(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.lines_path = path
            self.load_data()

    
    def _build_layout(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.overview_tab = ttk.Frame(self.notebook)
        self.centrality_tab = ttk.Frame(self.notebook)
        self.contingency_tab = ttk.Frame(self.notebook)
        self.map_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.overview_tab, text="Overview")
        self.notebook.add(self.centrality_tab, text="Centrality")
        self.notebook.add(self.contingency_tab, text="N-1 Contingency")
        self.notebook.add(self.map_tab, text="Network Diagram")

        self._build_overview_tab()
        self._build_centrality_tab()
        self._build_contingency_tab()
        self._build_map_tab()

    def load_data(self):
        try:
            substations, lines = na.load_data(self.substations_path, self.lines_path)
            self.G = na.build_graph(substations, lines)
            self.centrality_df = na.compute_centrality(self.G)
            self.summary = na.network_summary(self.G)
            self.bridges = na.find_bridges(self.G)
            self.layout_pos = self._compute_layout()
        except FileNotFoundError as e:
            messagebox.showerror("File not found", str(e))
            self.status_var.set("Failed to load data - check File menu to select CSVs.")
            return
        except Exception as e:
            messagebox.showerror("Error loading data", f"{type(e).__name__}: {e}")
            self.status_var.set("Failed to load data.")
            return

        self.status_var.set(
            f"Loaded {self.G.number_of_nodes()} substations, {self.G.number_of_edges()} lines "
            f"from '{self.substations_path}' / '{self.lines_path}'."
        )
        self._refresh_overview()
        self._refresh_centrality_table()
        self._refresh_contingency_selector()
        self._draw_network(highlight_node=None)

    def _compute_layout(self):
        """Prefer real geography if lat/lon is present, else spring layout."""
        has_coords = all(
            self.G.nodes[n].get("latitude") is not None
            and self.G.nodes[n].get("longitude") is not None
            for n in self.G.nodes()
        )
        if has_coords:
            return {n: (self.G.nodes[n]["longitude"], self.G.nodes[n]["latitude"]) for n in self.G.nodes()}
        return nx.spring_layout(self.G, seed=42)

   
    def _build_overview_tab(self):
        frame = self.overview_tab
        ttk.Label(frame, text="Network Overview", font=("TkDefaultFont", 14, "bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        self.overview_text = tk.Text(frame, height=16, wrap="word", state="disabled")
        self.overview_text.pack(fill="both", expand=True, padx=12, pady=6)

        caveat = (
            "Note: these are graph-structural measures (degree, betweenness, closeness, "
            "PageRank, connectivity). They do not represent electrical load, voltage stability, "
            "or real-time power flow, and should be read as reliability proxies, not definitive "
            "operational findings."
        )
        ttk.Label(frame, text=caveat, wraplength=1000, foreground="#555").pack(
            anchor="w", padx=12, pady=(0, 12)
        )

    def _refresh_overview(self):
        s = self.summary
        lines_status_counts = self.status_counts()
        text = (
            f"Substations (nodes): {s['num_substations']}\n"
            f"Transmission/distribution lines (edges): {s['num_lines']}\n"
            f"Network density: {s['density']:.4f}\n\n"
            f"Connected components: {s['num_connected_components']}\n"
            f"Largest connected component: {s['largest_component_size']} substations "
            f"({s['largest_component_size'] / s['num_substations']:.0%} of the network)\n"
            f"Isolated substations (no lines at all): {', '.join(s['isolated_substations']) or 'none'}\n\n"
            f"Diameter of largest component: {s['diameter_largest_component']}\n"
            f"Average shortest path (largest component): "
            f"{s['avg_shortest_path_largest_component']:.2f}\n" if s['avg_shortest_path_largest_component'] else
            f"Average shortest path (largest component): n/a\n"
        )
        text += (
            f"Average clustering coefficient: {s['average_clustering']:.4f}\n"
            f"Bridge lines (single point of failure): {s['num_bridges']}\n"
        )
        if self.bridges:
            bridge_str = ", ".join(f"{u}-{v}" for u, v in self.bridges)
            text += f"  -> {bridge_str}\n"
        if lines_status_counts:
            text += "\nLine status breakdown:\n"
            for status, count in lines_status_counts.items():
                text += f"  {status}: {count}\n"

        if s["num_connected_components"] > 1:
            text += (
                "\nInterpretation: the network as loaded is ALREADY fragmented into "
                f"{s['num_connected_components']} separate components before any contingency is "
                "simulated. This usually means some substations only connect to others outside "
                "the largest group, or the dataset has a genuinely disconnected regional segment - "
                "worth flagging in the data-quality report."
            )
        else:
            text += "\nInterpretation: the network is a single connected component."

        self.overview_text.configure(state="normal")
        self.overview_text.delete("1.0", "end")
        self.overview_text.insert("1.0", text)
        self.overview_text.configure(state="disabled")

    def status_counts(self):
        try:
            counts = {}
            for _, _, data in self.G.edges(data=True):
                st = data.get("status", "Unknown")
                counts[st] = counts.get(st, 0) + 1
            return counts
        except Exception:
            return {}

   
    def _build_centrality_tab(self):
        frame = self.centrality_tab
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=12, pady=(12, 4))

        ttk.Label(top, text="Sort by:").pack(side="left")
        self.sort_var = tk.StringVar(value="betweenness_centrality")
        sort_options = [
            "degree", "degree_centrality", "betweenness_centrality",
            "closeness_centrality", "eigenvector_centrality", "pagerank",
            "clustering_coefficient",
        ]
        sort_combo = ttk.Combobox(top, textvariable=self.sort_var, values=sort_options, state="readonly", width=26)
        sort_combo.pack(side="left", padx=6)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_centrality_table())

        ttk.Label(top, text="Filter region:").pack(side="left", padx=(16, 0))
        self.region_filter_var = tk.StringVar(value="All")
        self.region_filter_combo = ttk.Combobox(top, textvariable=self.region_filter_var, state="readonly", width=18)
        self.region_filter_combo.pack(side="left", padx=6)
        self.region_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_centrality_table())

        columns = (
            "substation_id", "name", "region", "degree", "degree_centrality",
            "betweenness_centrality", "closeness_centrality", "eigenvector_centrality",
            "pagerank", "clustering_coefficient",
        )
        headers = {
            "substation_id": "ID", "name": "Name", "region": "Region", "degree": "Degree",
            "degree_centrality": "Degree Cent.", "betweenness_centrality": "Betweenness",
            "closeness_centrality": "Closeness", "eigenvector_centrality": "Eigenvector",
            "pagerank": "PageRank", "clustering_coefficient": "Clustering",
        }
        self.centrality_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.centrality_tree.heading(col, text=headers[col])
            width = 160 if col == "name" else 100
            self.centrality_tree.column(col, width=width, anchor="center" if col != "name" else "w")
        self.centrality_tree.pack(fill="both", expand=True, padx=12, pady=6)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.centrality_tree.yview)
        self.centrality_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(in_=self.centrality_tree, relx=1.0, rely=0, relheight=1.0, anchor="ne")

        self.centrality_tree.bind("<Double-1>", self._on_centrality_row_selected)

        ttk.Label(
            frame,
            text="Double-click a row to jump to it in the N-1 Contingency tab.",
            foreground="#555",
        ).pack(anchor="w", padx=12, pady=(0, 8))

    def _refresh_centrality_table(self):
        if self.centrality_df is None:
            return
        regions = ["All"] + sorted(self.centrality_df["region"].dropna().unique().tolist())
        self.region_filter_combo.configure(values=regions)

        df = self.centrality_df.copy()
        region = self.region_filter_var.get()
        if region and region != "All":
            df = df[df["region"] == region]

        sort_col = self.sort_var.get()
        if sort_col in df.columns:
            df = df.sort_values(sort_col, ascending=False)

        for row in self.centrality_tree.get_children():
            self.centrality_tree.delete(row)

        for sub_id, row in df.iterrows():
            values = (
                sub_id, row["name"], row["region"], row["degree"],
                self._fmt(row["degree_centrality"]), self._fmt(row["betweenness_centrality"]),
                self._fmt(row["closeness_centrality"]), self._fmt(row["eigenvector_centrality"]),
                self._fmt(row["pagerank"]), self._fmt(row["clustering_coefficient"]),
            )
            self.centrality_tree.insert("", "end", values=values)

    @staticmethod
    def _fmt(x):
        try:
            return f"{float(x):.4f}"
        except (TypeError, ValueError):
            return "n/a"

    def _on_centrality_row_selected(self, event):
        item = self.centrality_tree.selection()
        if not item:
            return
        values = self.centrality_tree.item(item[0], "values")
        sub_id = values[0]
        self.contingency_selector_var.set(sub_id)
        self.notebook.select(self.contingency_tab)
        self.run_contingency()

   
    def _build_contingency_tab(self):
        frame = self.contingency_tab

        controls = ttk.Frame(frame)
        controls.pack(fill="x", padx=12, pady=12)

        ttk.Label(controls, text="Remove substation:").pack(side="left")
        self.contingency_selector_var = tk.StringVar()
        self.contingency_selector = ttk.Combobox(
            controls, textvariable=self.contingency_selector_var, state="readonly", width=30
        )
        self.contingency_selector.pack(side="left", padx=6)

        ttk.Button(controls, text="Run N-1 Simulation", command=self.run_contingency).pack(
            side="left", padx=10
        )
        ttk.Button(
            controls, text="Run Full N-1 Report (all substations)", command=self.run_full_contingency
        ).pack(side="left", padx=6)

        self.contingency_result_text = tk.Text(frame, height=10, wrap="word", state="disabled")
        self.contingency_result_text.pack(fill="x", padx=12, pady=6)

        ttk.Label(frame, text="Full N-1 report (most disruptive substations first):").pack(
            anchor="w", padx=12, pady=(6, 0)
        )
        columns = (
            "substation_id", "name", "components_before", "components_after",
            "largest_cc_before", "largest_cc_after", "fragments_network", "substations_cut_off",
        )
        headers = {
            "substation_id": "ID", "name": "Name", "components_before": "Comp. Before",
            "components_after": "Comp. After", "largest_cc_before": "Largest CC Before",
            "largest_cc_after": "Largest CC After", "fragments_network": "Fragments?",
            "substations_cut_off": "Substations Cut Off",
        }
        self.contingency_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.contingency_tree.heading(col, text=headers[col])
            self.contingency_tree.column(col, width=120, anchor="center")
        self.contingency_tree.pack(fill="both", expand=True, padx=12, pady=6)
        self.contingency_tree.bind("<Double-1>", self._on_full_report_row_selected)

    def _refresh_contingency_selector(self):
        options = sorted(
            f"{n} - {self.G.nodes[n].get('name', n)}" for n in self.G.nodes()
        )
        self.contingency_selector["values"] = options
        if options:
            self.contingency_selector_var.set(options[0])

    def _selected_node_id(self) -> str | None:
        val = self.contingency_selector_var.get()
        if not val:
            return None
        return val.split(" - ")[0]

    def run_contingency(self):
        node = self._selected_node_id()
        if node is None or self.G is None:
            return
        try:
            result = na.n1_contingency_single(self.G, node)
        except KeyError as e:
            messagebox.showerror("Substation not found", str(e))
            return

        lines = [
            f"Simulated removal of {result.removed_node} ({result.removed_name})",
            "",
            f"Connected components before removal: {result.components_before}",
            f"Connected components after removal:  {result.components_after}",
            f"Largest connected group before: {result.largest_cc_before} substations",
            f"Largest connected group after:  {result.largest_cc_after} substations",
            f"Substations cut off from the main network: {result.substations_cut_off}",
        ]
        if result.newly_isolated:
            lines.append(f"Newly isolated substations: {', '.join(result.newly_isolated)}")
        lines.append("")
        if result.fragments_network:
            lines.append(
                "RESULT: The network FRAGMENTS if this substation is lost - it is a single "
                "point of failure for at least one other substation's connectivity."
            )
        else:
            lines.append(
                "RESULT: The network remains a single connected component if this substation "
                "is lost - other substations retain a path to the rest of the network."
            )
        lines.append(
            "\n(This is a simplified graph-based N-1 check: connectivity only, not a "
            "power-flow, voltage-stability, or protection-coordination study.)"
        )

        self.contingency_result_text.configure(state="normal")
        self.contingency_result_text.delete("1.0", "end")
        self.contingency_result_text.insert("1.0", "\n".join(lines))
        self.contingency_result_text.configure(state="disabled")

        self._draw_network(highlight_node=node)

    def run_full_contingency(self):
        if self.G is None:
            return
        self.status_var.set("Running full N-1 report for all substations...")
        self.update_idletasks()
        df = na.n1_contingency_full(self.G)

        for row in self.contingency_tree.get_children():
            self.contingency_tree.delete(row)
        for sub_id, row in df.iterrows():
            self.contingency_tree.insert(
                "", "end",
                values=(
                    sub_id, row["name"], row["components_before"], row["components_after"],
                    row["largest_cc_before"], row["largest_cc_after"],
                    "YES" if row["fragments_network"] else "no", row["substations_cut_off"],
                ),
            )
        n_fragmenting = int(df["fragments_network"].sum())
        self.status_var.set(
            f"Full N-1 report complete: {n_fragmenting} of {len(df)} substations are single "
            "points of failure (their removal fragments the network)."
        )

    def _on_full_report_row_selected(self, event):
        item = self.contingency_tree.selection()
        if not item:
            return
        values = self.contingency_tree.item(item[0], "values")
        sub_id, name = values[0], values[1]
        self.contingency_selector_var.set(f"{sub_id} - {name}")
        self.run_contingency()

   
    def _build_map_tab(self):
        frame = self.map_tab
        self.fig = plt.Figure(figsize=(9, 6.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    def _draw_network(self, highlight_node: str | None):
        if self.G is None or self.layout_pos is None:
            return
        self.ax.clear()

        node_colors = []
        for n in self.G.nodes():
            if n == highlight_node:
                node_colors.append("red")
            else:
                node_colors.append("#4C72B0")

        edge_colors = []
        edge_widths = []
        Gdraw = self.G
        for u, v in Gdraw.edges():
            if highlight_node in (u, v):
                edge_colors.append("#cccccc")
                edge_widths.append(0.5)
            else:
                edge_colors.append("#888888")
                edge_widths.append(1.0)

        nx.draw_networkx_edges(Gdraw, self.layout_pos, ax=self.ax, edge_color=edge_colors, width=edge_widths)
        nx.draw_networkx_nodes(
            Gdraw, self.layout_pos, ax=self.ax, node_color=node_colors, node_size=120,
        )
        nx.draw_networkx_labels(Gdraw, self.layout_pos, ax=self.ax, font_size=6)

        title = "National Grid Substation Network"
        if highlight_node:
            title += f"  (highlighted: {highlight_node} — {self.G.nodes[highlight_node].get('name', '')})"
        self.ax.set_title(title, fontsize=10)
        self.ax.axis("off")
        self.canvas.draw()


def main():
    substations_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SUBSTATIONS
    lines_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_LINES
    app = GridNetworkApp(substations_path, lines_path)
    app.mainloop()


if __name__ == "__main__":
    main()
