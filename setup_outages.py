import sqlite3

conn = sqlite3.connect(r"C:\Users\barim\Downloads\grid (3).db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE outages (
    outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    line_id TEXT,
    substation_id TEXT,
    reported_time TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (line_id) REFERENCES lines(line_id),
    FOREIGN KEY (substation_id) REFERENCES substations(substation_id)
)
""")

cursor.execute("""
CREATE TABLE work_orders (
    work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER NOT NULL,
    assigned_to TEXT,
    created_time TEXT NOT NULL,
    status TEXT NOT NULL,
    resolved_time TEXT,
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id)
)
""")

conn.commit()
conn.close()
print("Tables created!")