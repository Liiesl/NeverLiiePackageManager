import sqlite3
import logging
from pathlib import Path

# Config matching your project
NLPM_HOME = Path.home() / ".nlpm"
REGISTRY_DB = NLPM_HOME / "registry.db"

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("migration")

def migrate():
    if not REGISTRY_DB.exists():
        logger.error(f"Database not found at {REGISTRY_DB}. Nothing to migrate.")
        return

    logger.info(f"Connecting to {REGISTRY_DB}...")
    conn = sqlite3.connect(REGISTRY_DB)
    cursor = conn.cursor()

    # List of new columns to add to 'libraries' table
    # format: (column_name, column_type)
    new_columns = [
        ("language", "TEXT"),
        ("framework", "TEXT"),
        ("author", "TEXT"),
        ("license", "TEXT"),
        ("keywords", "TEXT")
    ]

    updated_count = 0

    for col_name, col_type in new_columns:
        try:
            # SQLite does not support "IF NOT EXISTS" in ALTER TABLE
            # So we wrap it in a try/except block
            cursor.execute(f"ALTER TABLE libraries ADD COLUMN {col_name} {col_type}")
            logger.info(f"Added column: {col_name}")
            updated_count += 1
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info(f"Column '{col_name}' already exists. Skipping.")
            else:
                logger.error(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    
    if updated_count > 0:
        logger.info(f"Migration complete. Added {updated_count} columns.")
    else:
        logger.info("Database is already up to date.")

if __name__ == "__main__":
    migrate()