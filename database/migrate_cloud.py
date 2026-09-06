"""
Cloud MySQL Database Initializer & Migration Script
Run this script to automatically apply schema and seed data to any cloud MySQL database
(e.g., TiDB Cloud, Aiven, Railway, AWS RDS, etc.)

Usage:
  python database/migrate_cloud.py
"""

import os
import sys
import mysql.connector
from dotenv import load_dotenv

# Load backend/.env if available
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

def run_sql_file(cursor, filepath):
    print(f"--> Executing {os.path.basename(filepath)}...")
    with open(filepath, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split statements by semicolon (ignoring semicolons inside quotes is standard in these schema files)
    statements = sql_content.split(";")
    for stmt in statements:
        cleaned = stmt.strip()
        if cleaned:
            try:
                cursor.execute(cleaned)
            except mysql.connector.Error as e:
                # Ignore table already exists or harmless warnings
                if "already exists" in str(e) or "Duplicate" in str(e):
                    continue
                else:
                    print(f"    [Warning] {e}")


def main():
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "stock_app")
    ssl_mode = os.getenv("DB_SSL", "").lower()

    print("==================================================")
    print(" Cloud MySQL Initializer & Migration Tool")
    print("==================================================")
    print(f" Host:     {host}")
    print(f" Port:     {port}")
    print(f" User:     {user}")
    print(f" Database: {database}")
    print("==================================================")

    ssl_kwargs = {}
    is_remote = host not in ("localhost", "127.0.0.1")
    if ssl_mode in ("true", "1", "yes") or (ssl_mode != "false" and is_remote):
        ssl_kwargs["ssl_disabled"] = False
        ssl_kwargs["ssl_verify_cert"] = False

    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            **ssl_kwargs
        )
        cursor = conn.cursor()
        print("[OK] Successfully connected to MySQL database!")

        base_dir = os.path.dirname(__file__)
        schema_path = os.path.join(base_dir, "schema.sql")
        indexes_path = os.path.join(base_dir, "schema_indexes.sql")
        seed_path = os.path.join(base_dir, "seed.sql")

        if os.path.exists(schema_path):
            run_sql_file(cursor, schema_path)
        if os.path.exists(indexes_path):
            run_sql_file(cursor, indexes_path)
        if os.path.exists(seed_path):
            run_sql_file(cursor, seed_path)

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[SUCCESS] Cloud database initialized and seeded successfully!")

    except mysql.connector.Error as err:
        print(f"\n[ERROR] Database connection failed: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
