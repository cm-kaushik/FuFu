import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    host = os.getenv("DB_HOST", "localhost")
    port_env = os.getenv("DB_PORT")
    if port_env:
        port = int(port_env)
    elif "tidbcloud.com" in host:
        port = 4000
    else:
        port = 3306

    config = {
        "host": host,
        "port": port,
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "stock_app"),
    }
    # Enable SSL for cloud databases (TiDB, Aiven, etc.) if requested or if host is remote
    ssl_mode = os.getenv("DB_SSL", "").lower()
    is_remote = config["host"] not in ("localhost", "127.0.0.1")
    if ssl_mode in ("true", "1", "yes") or (ssl_mode != "false" and is_remote):
        config["ssl_disabled"] = False
        config["ssl_verify_cert"] = False
    return config

DB_CONFIG = get_db_config()

connection_pool = None


def init_pool():
    """Initialize the MySQL connection pool."""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="stock_app_pool",
            pool_size=5,
            pool_reset_session=True,
            **DB_CONFIG
        )
        print("[OK] MySQL connection pool created successfully")
    except mysql.connector.Error as err:
        print(f"[ERROR] Error creating connection pool: {err}")
        raise


def get_db():
    """FastAPI dependency that yields a database connection from the pool."""
    global connection_pool
    if connection_pool is None:
        init_pool()
    conn = connection_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_connection():
    """Get a direct connection (for non-FastAPI contexts)."""
    global connection_pool
    if connection_pool is None:
        init_pool()
    return connection_pool.get_connection()
