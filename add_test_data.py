import sqlite3

conn = sqlite3.connect(r"C:\Users\barim\Downloads\grid (3).db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO outages (line_id, reported_time, status, description)
VALUES ('L001', '2026-08-25 10:00', 'reported', 'Line L001 tripped due to overload')
""")

cursor.execute("""
INSERT INTO work_orders (outage_id, assigned_to, created_time, status)
VALUES (1, 'Benedicta', '2026-08-25 10:15', 'in_progress')
""")

conn.commit()
conn.close()
print("Test data inserted!")
