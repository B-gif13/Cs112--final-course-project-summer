<<<<<<< HEAD
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


conn = sqlite3.connect("grid.db")


utilities = pd.read_sql_query(
    "SELECT * FROM utilities",
    conn
)

substations = pd.read_sql_query(
    "SELECT * FROM substations",
    conn
)

lines = pd.read_sql_query(
    "SELECT * FROM lines",
    conn
)

print("Datasets loaded successfully.")

print("\nUtilities:")
print(utilities.head())

print("\nSubstations:")
print(substations.head())

print("\nLines:")
print(lines.head())



substations_with_utilities = substations.merge(
    utilities[["utility_id", "utility_name"]],
    on="utility_id",
    how="left"
)


utility_footprint = (
    substations_with_utilities["utility_name"]
    .value_counts()
)

print("\n===================================")
print("UTILITY FOOTPRINT")
print("===================================")
print(utility_footprint)



utility_footprint.plot(kind="bar")

plt.title("Number of Substations by Utility")
plt.xlabel("Utility")
plt.ylabel("Number of Substations")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("utility_footprint.png")
plt.show()



utility_footprint.to_csv(
    "utility_footprint.csv",
    header=["Number of Substations"]
)

utility_region = (
    substations_with_utilities
    .groupby(["utility_name", "region"])
    .size()
    .reset_index(name="substation_count")
)

print("\n===================================")
print("UTILITY FOOTPRINT BY REGION")
print("===================================")
print(utility_region)



utility_region.to_csv(
    "utility_footprint_by_region.csv",
    index=False
)



print("\n===================================")
print("SUBSTATION CAPACITY SUMMARY")
print("===================================")

print(substations["capacity_mva"].describe())




highest_capacity = (
    substations[
        [
            "substation_id",
            "substation_name",
            "region",
            "capacity_mva"
        ]
    ]
    .sort_values(
        by="capacity_mva",
        ascending=False
    )
)

print("\nHIGHEST-CAPACITY SUBSTATIONS:")
print(highest_capacity.head(10))


highest_capacity.head(10).to_csv(
    "highest_capacity_substations.csv",
    index=False
)



substations["capacity_mva"].plot(
    kind="hist",
    bins=6
)

plt.title("Distribution of Substation Capacity")
plt.xlabel("Capacity (MVA)")
plt.ylabel("Number of Substations")
plt.tight_layout()
plt.savefig("capacity_distribution.png")
plt.show()

capacity_by_region = (
    substations
    .groupby("region")["capacity_mva"]
    .sum()
    .sort_values(ascending=False)
)

print("\n===================================")
print("TOTAL RATED CAPACITY BY REGION")
print("===================================")
print(capacity_by_region)


capacity_by_region.plot(kind="bar")

plt.title("Total Rated Substation Capacity by Region")
plt.xlabel("Region")
plt.ylabel("Total Capacity (MVA)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("capacity_by_region.png")
plt.show()


capacity_by_region.to_csv(
    "capacity_by_region.csv",
    header=["Total Capacity MVA"]
)

average_capacity_region = (
    substations
    .groupby("region")["capacity_mva"]
    .mean()
    .sort_values(ascending=False)
)

print("\n===================================")
print("AVERAGE CAPACITY BY REGION")
print("===================================")
print(average_capacity_region)


average_capacity_region.to_csv(
    "average_capacity_by_region.csv",
    header=["Average Capacity MVA"]
)

substations_by_region = (
    substations["region"]
    .value_counts()
    .sort_values()
)

print("\n===================================")
print("NUMBER OF SUBSTATIONS BY REGION")
print("===================================")
print(substations_by_region)


substations_by_region.plot(kind="bar")

plt.title("Number of Substations by Region")
plt.xlabel("Region")
plt.ylabel("Number of Substations")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("substations_by_region.png")
plt.show()


substations_by_region.to_csv(
    "substations_by_region.csv",
    header=["Number of Substations"]
)

fewest_substations = substations_by_region.head(3)

print("\nREGIONS WITH THE FEWEST SUBSTATIONS:")
print(fewest_substations)
print("\n===================================")
print("ASSET AGE PROFILE")
print("===================================")

print(
    "Asset age analysis cannot currently be completed "
    "because the database does not contain Commissioning Year."
)

line_status = lines["status"].value_counts()

print("\n===================================")
print("LINE STATUS")
print("===================================")
print(line_status)


# Calculate percentages
line_status_percentage = (
    lines["status"]
    .value_counts(normalize=True)
    * 100
)

print("\nLINE STATUS PERCENTAGES:")
print(line_status_percentage.round(2))


line_status.plot(kind="bar")

plt.title("Operational Status of Electricity Lines")
plt.xlabel("Status")
plt.ylabel("Number of Lines")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("line_status.png")
plt.show()


line_status_percentage.to_csv(
    "line_status_percentage.csv",
    header=["Percentage"]
)
print("\n===================================")
print("LINE LENGTH SUMMARY")
print("===================================")

print(lines["length_km"].describe())


# Histogram showing line lengths
lines["length_km"].plot(
    kind="hist",
    bins=10
)

plt.title("Distribution of Electricity Line Lengths")
plt.xlabel("Line Length (km)")
plt.ylabel("Number of Lines")
plt.tight_layout()
plt.savefig("line_length_distribution.png")
plt.show()

longest_lines = (
    lines
    .sort_values(
        by="length_km",
        ascending=False
    )
    .head(10)
)

print("\n===================================")
print("TOP 10 LONGEST LINES")
print("===================================")
print(longest_lines)


longest_lines.to_csv(
    "longest_lines.csv",
    index=False
)



maintenance_length = (
    lines
    .groupby("status")["length_km"]
    .agg(["count", "mean", "min", "max"])
)

print("\n===================================")
print("LINE LENGTH BY MAINTENANCE STATUS")
print("===================================")
print(maintenance_length)


maintenance_length.to_csv(
    "maintenance_length_analysis.csv"
)

lines["maintenance_flag"] = (
    lines["status"] == "Under Maintenance"
).astype(int)
minimum_length = lines["length_km"].min()
maximum_length = lines["length_km"].max()

lines["length_score"] = (
    (lines["length_km"] - minimum_length)
    /
    (maximum_length - minimum_length)
)

lines["reliability_priority_score"] = (
    0.70 * lines["maintenance_flag"]
    +
    0.30 * lines["length_score"]
)

priority_lines = (
    lines
    .sort_values(
        by="reliability_priority_score",
        ascending=False
    )
)


print("\n===================================")
print("LINES WITH HIGHEST RELIABILITY PRIORITY")
print("===================================")

print(
    priority_lines[
        [
            "line_id",
            "from_substation",
            "to_substation",
            "voltage_kv",
            "length_km",
            "status",
            "reliability_priority_score"
        ]
    ].head(10)
)


priority_lines.to_csv(
    "reliability_priority_lines.csv",
    index=False
)
total_capacity = substations["capacity_mva"].sum()


capacity_ranking = (
    substations
    .sort_values(
        by="capacity_mva",
        ascending=False
    )
    .copy()
)

capacity_ranking["capacity_share_percent"] = (
    capacity_ranking["capacity_mva"]
    /
    total_capacity
    * 100
)
capacity_ranking["cumulative_capacity_percent"] = (
    capacity_ranking["capacity_share_percent"]
    .cumsum()
)


print("\n===================================")
print("CAPACITY CONCENTRATION")
print("===================================")

print(
    capacity_ranking[
        [
            "substation_id",
            "substation_name",
            "region",
            "capacity_mva",
            "capacity_share_percent",
            "cumulative_capacity_percent"
        ]
    ].head(10)
)


capacity_ranking.to_csv(
    "capacity_concentration.csv",
    index=False
)

print("\n===================================")
print("CENTRALITY-BASED RELIABILITY")
print("===================================")

print(
    "Centrality will be added after the NetworkX analysis "
    "results are available."
)
print("\n===================================")
print("TASK 2.3 ANALYSIS COMPLETE")
print("===================================")

print(
    "Completed analyses:\n"
    "- Utility footprint by number of substations\n"
    "- Utility footprint by region\n"
    "- Substation capacity distribution\n"
    "- Total and average capacity by region\n"
    "- Regional substation distribution\n"
    "- Line maintenance status\n"
    "- Line length analysis\n"
    "- Maintenance and line-length comparison\n"
    "- Reliability priority proxy\n"
    "- Capacity concentration analysis\n"
)

print(
    "\nPending because required data are unavailable:\n"
    "- Actual capacity utilisation\n"
    "- Infrastructure age profile\n"
    "- Utility line ownership by voltage tier\n"
    "- Population/area-adjusted underserved-region analysis\n"
    "- Centrality-based reliability analysis"
)

=======
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


conn = sqlite3.connect("grid.db")


utilities = pd.read_sql_query(
    "SELECT * FROM utilities",
    conn
)

substations = pd.read_sql_query(
    "SELECT * FROM substations",
    conn
)

lines = pd.read_sql_query(
    "SELECT * FROM lines",
    conn
)

print("Datasets loaded successfully.")

print("\nUtilities:")
print(utilities.head())

print("\nSubstations:")
print(substations.head())

print("\nLines:")
print(lines.head())



substations_with_utilities = substations.merge(
    utilities[["utility_id", "utility_name"]],
    on="utility_id",
    how="left"
)


utility_footprint = (
    substations_with_utilities["utility_name"]
    .value_counts()
)

print("\n===================================")
print("UTILITY FOOTPRINT")
print("===================================")
print(utility_footprint)



utility_footprint.plot(kind="bar")

plt.title("Number of Substations by Utility")
plt.xlabel("Utility")
plt.ylabel("Number of Substations")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("utility_footprint.png")
plt.show()



utility_footprint.to_csv(
    "utility_footprint.csv",
    header=["Number of Substations"]
)

utility_region = (
    substations_with_utilities
    .groupby(["utility_name", "region"])
    .size()
    .reset_index(name="substation_count")
)

print("\n===================================")
print("UTILITY FOOTPRINT BY REGION")
print("===================================")
print(utility_region)



utility_region.to_csv(
    "utility_footprint_by_region.csv",
    index=False
)



print("\n===================================")
print("SUBSTATION CAPACITY SUMMARY")
print("===================================")

print(substations["capacity_mva"].describe())




highest_capacity = (
    substations[
        [
            "substation_id",
            "substation_name",
            "region",
            "capacity_mva"
        ]
    ]
    .sort_values(
        by="capacity_mva",
        ascending=False
    )
)

print("\nHIGHEST-CAPACITY SUBSTATIONS:")
print(highest_capacity.head(10))


highest_capacity.head(10).to_csv(
    "highest_capacity_substations.csv",
    index=False
)



substations["capacity_mva"].plot(
    kind="hist",
    bins=6
)

plt.title("Distribution of Substation Capacity")
plt.xlabel("Capacity (MVA)")
plt.ylabel("Number of Substations")
plt.tight_layout()
plt.savefig("capacity_distribution.png")
plt.show()

capacity_by_region = (
    substations
    .groupby("region")["capacity_mva"]
    .sum()
    .sort_values(ascending=False)
)

print("\n===================================")
print("TOTAL RATED CAPACITY BY REGION")
print("===================================")
print(capacity_by_region)


capacity_by_region.plot(kind="bar")

plt.title("Total Rated Substation Capacity by Region")
plt.xlabel("Region")
plt.ylabel("Total Capacity (MVA)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("capacity_by_region.png")
plt.show()


capacity_by_region.to_csv(
    "capacity_by_region.csv",
    header=["Total Capacity MVA"]
)

average_capacity_region = (
    substations
    .groupby("region")["capacity_mva"]
    .mean()
    .sort_values(ascending=False)
)

print("\n===================================")
print("AVERAGE CAPACITY BY REGION")
print("===================================")
print(average_capacity_region)


average_capacity_region.to_csv(
    "average_capacity_by_region.csv",
    header=["Average Capacity MVA"]
)

substations_by_region = (
    substations["region"]
    .value_counts()
    .sort_values()
)

print("\n===================================")
print("NUMBER OF SUBSTATIONS BY REGION")
print("===================================")
print(substations_by_region)


substations_by_region.plot(kind="bar")

plt.title("Number of Substations by Region")
plt.xlabel("Region")
plt.ylabel("Number of Substations")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("substations_by_region.png")
plt.show()


substations_by_region.to_csv(
    "substations_by_region.csv",
    header=["Number of Substations"]
)

fewest_substations = substations_by_region.head(3)

print("\nREGIONS WITH THE FEWEST SUBSTATIONS:")
print(fewest_substations)
print("\n===================================")
print("ASSET AGE PROFILE")
print("===================================")

print(
    "Asset age analysis cannot currently be completed "
    "because the database does not contain Commissioning Year."
)

line_status = lines["status"].value_counts()

print("\n===================================")
print("LINE STATUS")
print("===================================")
print(line_status)


# Calculate percentages
line_status_percentage = (
    lines["status"]
    .value_counts(normalize=True)
    * 100
)

print("\nLINE STATUS PERCENTAGES:")
print(line_status_percentage.round(2))


line_status.plot(kind="bar")

plt.title("Operational Status of Electricity Lines")
plt.xlabel("Status")
plt.ylabel("Number of Lines")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("line_status.png")
plt.show()


line_status_percentage.to_csv(
    "line_status_percentage.csv",
    header=["Percentage"]
)
print("\n===================================")
print("LINE LENGTH SUMMARY")
print("===================================")

print(lines["length_km"].describe())


# Histogram showing line lengths
lines["length_km"].plot(
    kind="hist",
    bins=10
)

plt.title("Distribution of Electricity Line Lengths")
plt.xlabel("Line Length (km)")
plt.ylabel("Number of Lines")
plt.tight_layout()
plt.savefig("line_length_distribution.png")
plt.show()

longest_lines = (
    lines
    .sort_values(
        by="length_km",
        ascending=False
    )
    .head(10)
)

print("\n===================================")
print("TOP 10 LONGEST LINES")
print("===================================")
print(longest_lines)


longest_lines.to_csv(
    "longest_lines.csv",
    index=False
)



maintenance_length = (
    lines
    .groupby("status")["length_km"]
    .agg(["count", "mean", "min", "max"])
)

print("\n===================================")
print("LINE LENGTH BY MAINTENANCE STATUS")
print("===================================")
print(maintenance_length)


maintenance_length.to_csv(
    "maintenance_length_analysis.csv"
)

lines["maintenance_flag"] = (
    lines["status"] == "Under Maintenance"
).astype(int)
minimum_length = lines["length_km"].min()
maximum_length = lines["length_km"].max()

lines["length_score"] = (
    (lines["length_km"] - minimum_length)
    /
    (maximum_length - minimum_length)
)

lines["reliability_priority_score"] = (
    0.70 * lines["maintenance_flag"]
    +
    0.30 * lines["length_score"]
)

priority_lines = (
    lines
    .sort_values(
        by="reliability_priority_score",
        ascending=False
    )
)


print("\n===================================")
print("LINES WITH HIGHEST RELIABILITY PRIORITY")
print("===================================")

print(
    priority_lines[
        [
            "line_id",
            "from_substation",
            "to_substation",
            "voltage_kv",
            "length_km",
            "status",
            "reliability_priority_score"
        ]
    ].head(10)
)


priority_lines.to_csv(
    "reliability_priority_lines.csv",
    index=False
)
total_capacity = substations["capacity_mva"].sum()


capacity_ranking = (
    substations
    .sort_values(
        by="capacity_mva",
        ascending=False
    )
    .copy()
)

capacity_ranking["capacity_share_percent"] = (
    capacity_ranking["capacity_mva"]
    /
    total_capacity
    * 100
)
capacity_ranking["cumulative_capacity_percent"] = (
    capacity_ranking["capacity_share_percent"]
    .cumsum()
)


print("\n===================================")
print("CAPACITY CONCENTRATION")
print("===================================")

print(
    capacity_ranking[
        [
            "substation_id",
            "substation_name",
            "region",
            "capacity_mva",
            "capacity_share_percent",
            "cumulative_capacity_percent"
        ]
    ].head(10)
)


capacity_ranking.to_csv(
    "capacity_concentration.csv",
    index=False
)

print("\n===================================")
print("CENTRALITY-BASED RELIABILITY")
print("===================================")

print(
    "Centrality will be added after the NetworkX analysis "
    "results are available."
)
print("\n===================================")
print("TASK 2.3 ANALYSIS COMPLETE")
print("===================================")

print(
    "Completed analyses:\n"
    "- Utility footprint by number of substations\n"
    "- Utility footprint by region\n"
    "- Substation capacity distribution\n"
    "- Total and average capacity by region\n"
    "- Regional substation distribution\n"
    "- Line maintenance status\n"
    "- Line length analysis\n"
    "- Maintenance and line-length comparison\n"
    "- Reliability priority proxy\n"
    "- Capacity concentration analysis\n"
)

print(
    "\nPending because required data are unavailable:\n"
    "- Actual capacity utilisation\n"
    "- Infrastructure age profile\n"
    "- Utility line ownership by voltage tier\n"
    "- Population/area-adjusted underserved-region analysis\n"
    "- Centrality-based reliability analysis"
)

>>>>>>> origin/business_analysis
conn.close()