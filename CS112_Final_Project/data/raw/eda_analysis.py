import pandas as pd
import matplotlib.pyplot as plt

utilities = pd.read_csv("utilities.csv")
substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")
print("UTILITIES DATASET")
print(utilities.head())
print("Shape:", utilities.shape)
print()

print("SUBSTATIONS DATASET")
print(substations.head())
print("Shape:", substations.shape)
print()

print("LINES DATASET")
print(lines.head())
print("Shape:", lines.shape)
print()

print("SUBSTATION NUMERICAL SUMMARY")
print(
    substations[
        ["capacity_mva", "latitude", "longitude"]
    ].describe()
)
print()

print("LINE NUMERICAL SUMMARY")
print(
    lines[
        ["voltage_kv", "length_km"]
    ].describe()
)
print()

utility_type_counts = utilities["type"].value_counts()

print("UTILITY TYPES")
print(utility_type_counts)
print()

utility_type_counts.plot(
    kind="bar",
    title="Number of Utilities by Type"
)

plt.xlabel("Utility Type")
plt.ylabel("Number of Utilities")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("utility_types.png")
plt.show()

region_counts = substations["region"].value_counts()

print("SUBSTATIONS BY REGION")
print(region_counts)
print()

region_counts.plot(
    kind="bar",
    title="Number of Substations by Region"
)

plt.xlabel("Region")
plt.ylabel("Number of Substations")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("substations_by_region.png")
plt.show()

substations_with_utilities = substations.merge(
    utilities[["utility_id", "utility_name"]],
    on="utility_id",
    how="left"
)

utility_substation_counts = (
    substations_with_utilities["utility_name"]
    .value_counts()
)

print("NUMBER OF SUBSTATIONS BY UTILITY")
print(utility_substation_counts)
print()

utility_substation_counts.plot(
    kind="bar",
    title="Number of Substations by Utility"
)

plt.xlabel("Utility")
plt.ylabel("Number of Substations")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("substations_by_utility.png")
plt.show()

capacity_counts = (
    substations["capacity_mva"]
    .value_counts()
    .sort_index()
)

print("SUBSTATION CAPACITY COUNTS")
print(capacity_counts)
print()

capacity_counts.plot(
    kind="bar",
    title="Substations by Capacity"
)

plt.xlabel("Capacity (MVA)")
plt.ylabel("Number of Substations")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("capacity_counts.png")
plt.show()

substations["capacity_mva"].plot(
    kind="hist",
    bins=6,
    edgecolor="black",
    title="Distribution of Substation Capacity"
)

plt.xlabel("Capacity (MVA)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("capacity_distribution.png")
plt.show()

total_capacity_by_region = (
    substations.groupby("region")["capacity_mva"]
    .sum()
    .sort_values(ascending=False)
)

print("TOTAL SUBSTATION CAPACITY BY REGION")
print(total_capacity_by_region)
print()

total_capacity_by_region.plot(
    kind="bar",
    title="Total Substation Capacity by Region"
)

plt.xlabel("Region")
plt.ylabel("Total Capacity (MVA)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("total_capacity_by_region.png")
plt.show()

average_capacity_by_region = (
    substations.groupby("region")["capacity_mva"]
    .mean()
    .sort_values(ascending=False)
)

print("AVERAGE SUBSTATION CAPACITY BY REGION")
print(average_capacity_by_region)
print()

average_capacity_by_region.plot(
    kind="bar",
    title="Average Substation Capacity by Region"
)

plt.xlabel("Region")
plt.ylabel("Average Capacity (MVA)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("average_capacity_by_region.png")
plt.show()

voltage_counts = (
    lines["voltage_kv"]
    .value_counts()
    .sort_index()
)

print("LINES BY VOLTAGE LEVEL")
print(voltage_counts)
print()

voltage_counts.plot(
    kind="bar",
    title="Electricity Lines by Voltage Level"
)

plt.xlabel("Voltage (kV)")
plt.ylabel("Number of Lines")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("line_voltage_distribution.png")
plt.show()

line_status_counts = lines["status"].value_counts()

print("LINE STATUS")
print(line_status_counts)
print()

line_status_counts.plot(
    kind="bar",
    title="Status of Electricity Lines"
)

plt.xlabel("Status")
plt.ylabel("Number of Lines")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("line_status.png")
plt.show()

line_status_percentages = (
    lines["status"].value_counts(normalize=True) * 100
)

print("LINE STATUS PERCENTAGES")
print(line_status_percentages.round(2))
print()
lines["length_km"].plot(
    kind="hist",
    bins=10,
    edgecolor="black",
    title="Distribution of Electricity Line Lengths"
)

plt.xlabel("Line Length (km)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("line_length_distribution.png")
plt.show()

all_connected_substations = pd.concat(
    [
        lines["from_substation"],
        lines["to_substation"]
    ]
)

connection_counts = all_connected_substations.value_counts()

top_connected = connection_counts.head(10)

print("TOP 10 MOST-CONNECTED SUBSTATIONS")
print(top_connected)
print()

top_connected_table = (
    top_connected
    .rename_axis("substation_id")
    .reset_index(name="number_of_connections")
)

top_connected_table = top_connected_table.merge(
    substations[
        ["substation_id", "substation_name", "region"]
    ],
    on="substation_id",
    how="left"
)

print("TOP CONNECTED SUBSTATIONS WITH NAMES")
print(top_connected_table)
print()

top_connected_table.plot(
    kind="bar",
    x="substation_name",
    y="number_of_connections",
    legend=False,
    title="Top 10 Most-Connected Substations"
)

plt.xlabel("Substation")
plt.ylabel("Number of Connections")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("most_connected_substations.png")
plt.show()
region_counts.to_csv("region_counts.csv")

utility_substation_counts.to_csv(
    "utility_substation_counts.csv"
)

total_capacity_by_region.to_csv(
    "total_capacity_by_region.csv"
)

average_capacity_by_region.to_csv(
    "average_capacity_by_region.csv"
)

voltage_counts.to_csv(
    "voltage_counts.csv"
)

line_status_counts.to_csv(
    "line_status_counts.csv"
)

top_connected_table.to_csv(
    "top_connected_substations.csv",
    index=False
)

print("EDA completed successfully.")
print("Charts and result tables have been saved.")
