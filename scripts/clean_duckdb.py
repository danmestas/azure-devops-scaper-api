import duckdb

# Path to your DuckDB database file.
db_path = "historical_data.duckdb"
conn = duckdb.connect(database=db_path, read_only=False)

# List of tables you want to drop.
tables = ["comments", "revisions", "work_item_tags", "work_items", "users"]

for table in tables:
    drop_sql = f"DROP TABLE IF EXISTS {table};"
    conn.execute(drop_sql)
    print(f"Table '{table}' dropped (if it existed).")

conn.close()
print("DuckDB cleaned: all specified tables have been dropped.") 