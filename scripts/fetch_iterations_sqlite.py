#!/usr/bin/env python3
import os
import sqlite3
import logging
from dotenv import load_dotenv
from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv(".env")
AZURE_DEVOPS_ORG     = os.getenv("AZURE_DEVOPS_ORG")
AZURE_DEVOPS_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
AZURE_DEVOPS_PAT     = os.getenv("AZURE_DEVOPS_PAT")

if not (AZURE_DEVOPS_ORG and AZURE_DEVOPS_PROJECT and AZURE_DEVOPS_PAT):
    logger.error("Missing Azure DevOps credentials in .env")
    exit(1)

# Connect to Azure DevOps using PAT
organization_url = f"https://dev.azure.com/{AZURE_DEVOPS_ORG}"
credentials = BasicAuthentication("", AZURE_DEVOPS_PAT)
connection_ado = Connection(base_url=organization_url, creds=credentials)
wit_client = connection_ado.clients.get_work_item_tracking_client()

# SQLite Database file path
DB_FILE = "historical_data.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create/verify iterations table
create_table_sql = """
CREATE TABLE IF NOT EXISTS iterations (
    iteration_id INTEGER PRIMARY KEY,
    name TEXT,
    path TEXT,
    start_date TEXT,
    finish_date TEXT,
    timeframe TEXT
);
"""
cursor.execute(create_table_sql)
conn.commit()
logger.info("Table 'iterations' created/verified.")

def fetch_iterations(project):
    """
    Fetch the root iteration node for the given project.
    Using a higher depth ensures that all child iterations are returned.
    Passing an empty path returns the root node containing all iterations.
    """
    try:
        root_node = wit_client.get_classification_node(
            project=project,
            structure_group="iterations",
            path="",      # Get the root node
            depth=10      # Retrieve children up to 10 levels deep.
        )
        return root_node
    except Exception as e:
        logger.error(f"Error fetching iterations: {e}")
        return None

def flatten_iterations(node):
    """
    Recursively flatten the iterations tree into a list of iteration metadata dictionaries.
    Expected keys include:
      - iteration_id, name, path,
      - start_date, finish_date, timeframe
    """
    iterations = []

    # Get metadata for the current iteration node (if attributes exist)
    iteration_data = {
        "iteration_id": node.id,
        "name": node.name,
        "path": node.path,
        "start_date": node.attributes.get("startDate") if hasattr(node, "attributes") and node.attributes else None,
        "finish_date": node.attributes.get("finishDate") if hasattr(node, "attributes") and node.attributes else None,
        "timeframe": node.attributes.get("timeFrame") if hasattr(node, "attributes") and node.attributes else None,
    }
    iterations.append(iteration_data)

    # Process child iterations, if any, recursively
    if hasattr(node, "children") and node.children:
        for child in node.children:
            iterations.extend(flatten_iterations(child))
    return iterations

def insert_iteration(iteration):
    """
    Insert or replace an iteration record into the iterations table.
    """
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO iterations (iteration_id, name, path, start_date, finish_date, timeframe)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            iteration["iteration_id"],
            iteration["name"],
            iteration["path"],
            iteration["start_date"],
            iteration["finish_date"],
            iteration["timeframe"]
        ))
        conn.commit()
        logger.info(f"Inserted iteration '{iteration['name']}' (ID: {iteration['iteration_id']}).")
    except Exception as e:
        logger.error(f"Error inserting iteration {iteration['iteration_id']}: {e}")

def main():
    root_node = fetch_iterations(AZURE_DEVOPS_PROJECT)
    if root_node:
        iteration_list = flatten_iterations(root_node)
        for iteration in iteration_list:
            insert_iteration(iteration)
    else:
        logger.error("Failed to fetch iteration data.")
    conn.close()
    logger.info("Finished fetching and storing iteration metadata.")

if __name__ == "__main__":
    main() 