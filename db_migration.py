from sqlalchemy import create_engine, inspect
import pandas as pd
import sqlite3
import json
import os

## Script to Migrate from Postgre to SQLite (for simpler deployment) ##

# PostgreSQL connection
POSTGRES_URI = os.getenv('POSTGRES_URI')
postgres_engine = create_engine(POSTGRES_URI)

# SQLite connection
SQLITE_DB_PATH = 'instance/data.db'
sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)

# Use SQLAlchemy's inspector to get list of tables
inspector = inspect(postgres_engine)
postgres_tables = inspector.get_table_names()

# Migrate each table
for table in postgres_tables:
    print(f"Migrating {table}...")

    # Load data from PostgreSQL
    df = pd.read_sql_table(table, postgres_engine)

    # Convert list-like columns to JSON strings or comma-separated values
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():  # Check if column contains lists
            print(f"Converting column '{col}' in table '{table}' to JSON strings...")
            df[col] = df[col].apply(json.dumps)  # Convert lists to JSON strings

    # Write data to SQLite
    df.to_sql(table, sqlite_conn, if_exists='replace', index=False)

sqlite_conn.close()
print("Migration completed successfully.")
