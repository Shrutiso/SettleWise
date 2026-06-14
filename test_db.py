import sqlite3

conn = sqlite3.connect("expenses.db")

cursor = conn.cursor()

print("TABLES:")
cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""")
print(cursor.fetchall())

print("\nEXPENSES:")
cursor.execute("SELECT COUNT(*) FROM expenses")
print(cursor.fetchone())

print("\nANOMALIES:")
cursor.execute("SELECT COUNT(*) FROM anomalies")
print(cursor.fetchone())

conn.close()