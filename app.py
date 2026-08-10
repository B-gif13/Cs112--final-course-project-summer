"""
GridCare Analytics Dashboard - National Electricity Grid Network Analysis
Owner: Aaron (Dashboard, Report & Presentation Lead)

Week 2 status: dashboard is wired to the team's ACTUAL committed files as of
Week 2 (verified against the real repo, not assumptions):

- Benedicta: grid.db at repo root, confirmed tables `utilities`,
  `substations`, `lines` matching the Week 1 CSV schema.
- Tayviah: her Week 2 folder `tayviahweek2/` contains an importable module
  `_networkanalysis.py` (centrality + N-1 contingency) and her own copies of
  substations.csv / lines.csv. Rather than wait for her to export static
  CSVs, this dashboard imports her module directly and calls her functions
  live — so her real analysis runs inside the app itself.
- Naeem: `business_analysis.py` at repo root is a Business Intelligence /
  capacity analysis script (utility footprint, capacity concentration,
  reliability priority scoring) — NOT the login/outage-status backend the
  Week 2 plan described. Flag this mismatch to the team; it's not something
  this dashboard can paper over. His script only produces its output CSVs
  when someone actually RUNS it — none were committed as of this write-up.
  This dashboard looks for those output CSVs and shows a clear "pending"
  state (with the exact filenames + one-line instruction) until they exist.

Run with: streamlit run app.py   (run from the repo root)

INTEGRATION NOTES FOR THE TEAM:
- If Benedicta's db file moves or is renamed, update DB_PATH below.
- If Tayviah's folder/files are renamed, update TAYVIAH_DIR / the two path
  constants below.
- Naeem needs to run `business_analysis.py` once and commit the resulting
  CSVs (listed in BUSINESS_FILES below) to the repo root for the Business
  Insights tab to populate.
"""

import importlib.util
import os
import sqlite3
import sys

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ghana National Grid Dashboard", layout="wide")

st.title("Ghana National Electricity Grid — Analysis Dashboard")
st.caption("Synthetic, seeded dataset for coursework purposes only — not real grid data.")

# ---------------------------------------------------------------------------
# CONFIG — matches the actual files currently in the repo (confirmed Week 2)
# ---------------------------------------------------------------------------
DB_PATH = "grid.db"                       # Benedicta — repo root
CSV_FALLBACK_DIR = "networkX graph"       # Week 1 CSVs, used only if grid.db is missing

TAYVIAH_DIR = "tayviahweek2"
TAYVIAH_MODULE_PATH = f"{TAYVIAH_DIR}/_networkanalysis.py"
TAYVIAH_SUBSTATIONS = f"{TAYVIAH_DIR}/substations.csv"
TAYVIAH_LINES = f"{TAYVIAH_DIR}/lines.csv"

# Files business_analysis.py produces when Naeem actually runs it.
# Dashboard shows each one as pending until it's committed to the repo root.
BUSINESS_FILES = {
    "Utility footprint by region": "utility_footprint_by_region.csv",
    "Total capacity by region": "capacity_by_region.csv",
    "Reliability priority lines": "reliability_priority_lines.csv",
    "Capacity concentration": "capacity_concentration.csv",
}


# ---------------------------------------------------------------------------
# DATA ACCESS — core grid data (SQLite primary, CSV fallback)
# ---------------------------------------------------------------------------
@st.cache_data
def load_core_data():
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        try:
            utilities = pd.read_sql("SELECT * FROM utilities", conn)
            substations = pd.read_sql("SELECT * FROM substations", conn)
            lines = pd.read_sql("SELECT * FROM lines", conn)
            return utilities, substations, lines, "database"
        except (pd.errors.DatabaseError, sqlite3.OperationalError):
            pass
        finally:
            conn.close()

    utilities = pd.read_csv(f"{CSV_FALLBACK_DIR}/utilities.csv")
    substations = pd.read_csv(f"{CSV_FALLBACK_DIR}/substations.csv")
    lines = pd.read_csv(f"{CSV_FALLBACK_DIR}/lines.csv")
    return utilities, substations, lines, "csv fallback"


# ---------------------------------------------------------------------------
# DATA ACCESS — Tayviah's network analysis, run live from her module
# ---------------------------------------------------------------------------
@st.cache_resource
def load_network_analysis():
    if not os.path.exists(TAYVIAH_MODULE_PATH):
        return None
    try:
        spec = importlib.util.spec_from_file_location("networkanalysis", TAYVIAH_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["networkanalysis"] = mod  # required before exec for @dataclass to resolve
        spec.loader.exec_module(mod)

        results = mod.run_full_analysis(TAYVIAH_SUBSTATIONS, TAYVIAH_LINES)
        contingency = mod.n1_contingency_full(results["graph"])
        return {
            "summary": results["summary"],
            "centrality": results["centrality"].reset_index(),
            "critical": results["critical"].reset_index(),
            "bridges": results["bridges"],
            "contingency": contingency.reset_index(),
        }
    except Exception as e:
        st.session_state["network_analysis_error"] = str(e)
        return None


# ---------------------------------------------------------------------------
# DATA ACCESS — Naeem's business analysis outputs (pending until committed)
# ---------------------------------------------------------------------------
@st.cache_data
def load_business_outputs():
    found = {}
    for label, filename in BUSINESS_FILES.items():
        if os.path.exists(filename):
            found[label] = pd.read_csv(filename)
    return found


utilities, substations, lines, core_source = load_core_data()
network = load_network_analysis()
business = load_business_outputs()

# ---------------------------------------------------------------------------
# SIDEBAR — integration status
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Team Integration Status")
    if core_source == "database":
        st.success(f"Core data: SQLite ({DB_PATH})")
    else:
        st.warning("Core data: CSV fallback — grid.db not found")

    if network is not None:
        st.success("Network analysis: live (Tayviah's module)")
    else:
        st.warning(f"Network analysis: pending — {TAYVIAH_MODULE_PATH} not found or failed to load")

    loaded_n = len(business)
    total_n = len(BUSINESS_FILES)
    if loaded_n == total_n:
        st.success(f"Business insights: loaded ({loaded_n}/{total_n} files)")
    elif loaded_n > 0:
        st.warning(f"Business insights: partial ({loaded_n}/{total_n} files)")
    else:
        st.warning("Business insights: pending — Naeem hasn't committed output CSVs yet")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Substations", "Network", "Vulnerability (N-1)", "Business Insights"]
)

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Utilities", len(utilities))
    col2.metric("Substations", len(substations))
    col3.metric("Lines", len(lines))
    active_pct = (lines["status"] == "Active").mean() * 100
    col4.metric("Lines Active", f"{active_pct:.1f}%")

    st.subheader("Substations by Region")
    st.bar_chart(substations["region"].value_counts())

    st.subheader("Lines by Voltage Level (kV)")
    st.bar_chart(lines["voltage_kv"].value_counts().sort_index())

with tab2:
    st.subheader("Substation Table")
    region_filter = st.multiselect(
        "Filter by region", options=sorted(substations["region"].unique())
    )
    filtered = substations[substations["region"].isin(region_filter)] if region_filter else substations
    st.dataframe(filtered)

    st.subheader("Capacity Distribution (MVA)")
    st.bar_chart(filtered["capacity_mva"].value_counts().sort_index())

with tab3:
    if network is not None:
        summary = network["summary"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Connected Components", summary["num_connected_components"])
        col2.metric("Largest Component", summary["largest_component_size"])
        col3.metric("Bridges", summary["num_bridges"])
        col4.metric("Isolated Substations", len(summary["isolated_substations"]))

        st.subheader("Top 10 Most Critical Substations (composite score)")
        st.dataframe(
            network["critical"][
                ["substation_id", "name", "region", "composite_criticality_score"]
            ]
        )

        st.subheader("Top 10 by Betweenness Centrality")
        st.dataframe(
            network["centrality"]
            .sort_values("betweenness_centrality", ascending=False)
            .head(10)[["substation_id", "name", "region", "betweenness_centrality"]]
        )
    else:
        st.info(
            f"Waiting on Tayviah's network analysis module at {TAYVIAH_MODULE_PATH}. "
            + st.session_state.get("network_analysis_error", "")
        )

with tab4:
    st.caption(
        "N-1 contingency analysis (live, from Tayviah's _networkanalysis.py): "
        "what happens to the grid's connectivity if a single substation is removed."
    )
    if network is not None:
        contingency = network["contingency"]
        st.subheader("Most Disruptive Substations to Lose")
        st.dataframe(
            contingency[
                ["substation_id", "name", "fragments_network",
                 "substations_cut_off", "largest_cc_drop", "newly_isolated"]
            ].head(10)
        )
        st.subheader("Substations Cut Off if Top Substation Fails")
        st.bar_chart(
            contingency.sort_values("substations_cut_off", ascending=False)
            .set_index("substation_id")["substations_cut_off"]
            .head(10)
        )
        if network["bridges"]:
            st.subheader("Bridge Lines (single points of failure)")
            st.write(network["bridges"])
    else:
        st.info(f"Waiting on Tayviah's network analysis module at {TAYVIAH_MODULE_PATH}.")

with tab5:
    st.caption(
        "Business/capacity insights from Naeem's business_analysis.py. "
        "Note: this covers utility footprint and capacity analysis, not the "
        "login/outage-status backend originally planned for Week 2 — worth "
        "confirming with the team."
    )
    if business:
        for label, df in business.items():
            st.subheader(label)
            st.dataframe(df.head(10))
    else:
        st.warning(
            "No business analysis outputs found yet. Naeem needs to run "
            "`business_analysis.py` once and commit these files to the repo root: "
            + ", ".join(BUSINESS_FILES.values())
        )
