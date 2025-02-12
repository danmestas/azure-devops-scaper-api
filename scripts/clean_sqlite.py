import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to your SQLite database file
DB_FILE = "ado_data.db"

def clean_database(db_file):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    # List all tables you want to drop
    tables = ["work_items", "revisions", "comments"]
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
            logger.info(f"Table '{table}' dropped (if it existed).")
        except Exception as e:
            logger.error(f"Error dropping table '{table}': {e}")

    connection.commit()
    connection.close()
    logger.info("SQLite database cleaned: all specified tables have been dropped.")

if __name__ == "__main__":
    clean_database(DB_FILE) 