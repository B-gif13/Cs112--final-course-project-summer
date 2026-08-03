import pandas as pd
import matplotlib.pyplot as plt

utilities=pd.read_csv("utilities.csv")
substations=pd.read_csv("substations.csv")
lines=pd.read_csv("lines.csv")

print("Utilities")
print(utilities.head())
print(utilities.shape)

print("\nSubstations")
print(substations.head())
print(substations.shape)

print("\nLines")
print(lines.head())
print(lines.shape)

print("\nSubstation Data")
print(substations.describe())

print("\nLine Data")
print(lines.describe())

region_count=substations["Region"].value_counts()

print('\nSubstation Count by Region')
print(region_count)

region_count.plot(kind='bar', title='Substation Count by Region')
plt.xlabel('Region')
plt.ylabel('Number of substations')
plt.tight_layout()
plt.savefig('substation_count_by_region.png')
plt.show()

voltage_count=substations["Voltage (kV)"].value_counts().sort_index()
print('\nSubstation Count by Voltage Level')
print(voltage_count)

voltage_count.plot(kind='bar', title='Substation Count by Voltage Level')
plt.xlabel('Voltage (kV)')
plt.ylabel('Number of substations')
plt.tight_layout()
plt.savefig('voltage_distribution.png')
plt.show()

status_count=substations["Status"].value_counts()
print('\nSubstation Count by Status')
print(status_count)

status_count.plot(kind='bar', title='Active/Inactive Substation Count')
plt.xlabel('Status')
plt.ylabel('Number of substations')
plt.tight_layout()
plt.savefig('substation_status.png')
plt.show()

utility_line_counts=lines["Utility ID"].value_counts().reset_index()
utility_line_counts.columns=["Utility ID", "Line Count"]

utility_results=utility_line_counts.merge(
    utilities[["Utility ID", "Name"]], on="Utility ID", how="left")

utility_result=utility_results.sort_values(by="Line Count", ascending=False)
print('\nLine Count by Utility')
print(utility_result)

utility_results.plot(
    kind="bar",
    x="Name",
    y="Line Count",
    legend=False
)

plt.title("Number of Lines Operated by Each Utility")
plt.xlabel("Utility")
plt.ylabel("Number of Lines")
plt.tight_layout()
plt.savefig("utilities_by_lines.png")
plt.show()

source_counts = lines["Source Substation"].value_counts()
destination_counts = lines["Destination Substation"].value_counts()

connection_counts = source_counts.add(
    destination_counts,
    fill_value=0
)

connection_counts = connection_counts.sort_values(
    ascending=False
)

top_connected = connection_counts.head(10)

print("\nTOP 10 MOST-CONNECTED SUBSTATIONS")
print(top_connected)

top_connected.plot(kind="bar")

plt.title("Top 10 Most-Connected Substations")
plt.xlabel("Substation")
plt.ylabel("Number of Connected Lines")
plt.tight_layout()
plt.savefig("most_connected_substations.png")
plt.show()

line_status = lines["Status"].value_counts()

print("\nLINE STATUS")
print(line_status)

line_status.plot(kind="bar")

plt.title("Status of Electricity Lines")
plt.xlabel("Status")
plt.ylabel("Number of Lines")
plt.tight_layout()
plt.savefig("line_status.png")
plt.show()

line_type_counts = lines["Line Type"].value_counts()

print("\nLINE TYPES")
print(line_type_counts)

line_type_counts.plot(kind="bar")

plt.title("Distribution of Line Types")
plt.xlabel("Line Type")
plt.ylabel("Number of Lines")
plt.tight_layout()
plt.savefig("line_types.png")
plt.show()

substations["Capacity (MVA)"].plot(kind="hist", bins=10)

plt.title("Distribution of Substation Capacity")
plt.xlabel("Capacity (MVA)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("capacity_distribution.png")
plt.show()

lines["Length (km)"].plot(kind="hist", bins=10)

plt.title("Distribution of Line Lengths")
plt.xlabel("Length (km)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("line_length_distribution.png")
plt.show()