"""Quick script to view all data in the SnapDrive SQLite database."""

import sqlite3

conn = sqlite3.connect("snapdrive.db")
cursor = conn.cursor()

# Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("=" * 50)
print(f"TABLES IN DATABASE: {tables}")
print("=" * 50)

for table in tables:
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()

    # Get column names
    col_names = [desc[0] for desc in cursor.description]

    print(f"\n--- {table.upper()} ({len(rows)} rows) ---")
    print(f"Columns: {col_names}")
    for row in rows:
        print(row)

conn.close()

 