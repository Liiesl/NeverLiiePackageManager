# src/db.py
import sqlite3
import logging
from . import config

logger = logging.getLogger("nlpm")

def get_conn():
    """Returns a connection to the SQLite database."""
    config.NLPM_HOME.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.REGISTRY_DB)
    conn.row_factory = sqlite3.Row
    return conn

def _add_column_if_not_exists(cursor, table, col_name, col_type):
    """Helper to migrate existing databases without crashing."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
    except sqlite3.OperationalError:
        # Column likely already exists
        pass

def init_db():
    """Creates the schema if it doesn't exist and migrates old schemas."""
    conn = get_conn()
    cursor = conn.cursor()
    
    # Table: libraries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS libraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        import_name TEXT, 
        description TEXT,
        language TEXT,
        framework TEXT,
        author TEXT,
        license TEXT,
        keywords TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migration: Ensure new columns exist for old databases
    _add_column_if_not_exists(cursor, "libraries", "language", "TEXT")
    _add_column_if_not_exists(cursor, "libraries", "framework", "TEXT")
    _add_column_if_not_exists(cursor, "libraries", "author", "TEXT")
    _add_column_if_not_exists(cursor, "libraries", "license", "TEXT")
    _add_column_if_not_exists(cursor, "libraries", "keywords", "TEXT")

    # Table: versions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        library_id INTEGER NOT NULL,
        version TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(library_id) REFERENCES libraries(id),
        UNIQUE(library_id, version)
    );
    """)

    # Table: package_files
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS package_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        FOREIGN KEY(version_id) REFERENCES versions(id)
    );
    """)
    
    conn.commit()
    conn.close()