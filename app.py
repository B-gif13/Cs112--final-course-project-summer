"""
GridCare Analytics Dashboard - National Electricity Grid Network Analysis
Owner: Aaron (Dashboard, Report & Presentation Lead)

Week 1 status: starter scaffold wired to the real datasets so the repo
has a running prototype from day one. Will be expanded in Week 3 with
Tayviah's network metrics and Naeem's EDA results as those are finalized.

Run with: streamlit run dashboard/app.py
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ghana National Grid Dashboard", layout="wide")

st.title("Ghana National Electricity Grid — Analysis Dashboard")
st.caption("Synthetic, seeded dataset for coursework purposes only — not real grid data.")


@st.cache_data
def load_data():
    utilities = pd.read_csv("networkX graph/utilities.csv")
    substations = pd.read_csv("networkX graph/substations.csv")
    lines = pd.read_csv("networkX graph/lines.csv")
    return utilities, substations, lines


utilities, substations, lines = load_data()

# --- Overview tab ---
tab1, tab2, tab3 = st.tabs(["Overview", "Substations", "Network"])

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
    st.info(
        "Network metrics (degree, betweenness, closeness centrality) will be "
        "pulled in from Tayviah's substation_centrality.csv output here in Week 3, "
        "along with the geographic and spring-layout network graphs."
    )
    try:
        centrality = pd.read_csv("networkX graph/substation_centrality.csv")
        st.subheader("Top 10 Substations by Betweenness Centrality")
        st.dataframe(
            centrality.sort_values("betweenness_centrality", ascending=False)
            .head(10)[["substation_id", "substation_name", "region", "betweenness_centrality"]]
        )
    except FileNotFoundError:
        st.warning("substation_centrality.csv not yet available.")
