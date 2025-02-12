#!/usr/bin/env python3
import os
import json
import sqlite3
import logging
from pprint import pprint
from dotenv import load_dotenv
from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv(".env")

AZURE_DEVOPS_ORG = os.getenv("AZURE_DEVOPS_ORG")
AZURE_DEVOPS_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT")

if not (AZURE_DEVOPS_ORG and AZURE_DEVOPS_PROJECT and AZURE_DEVOPS_PAT):
    logger.error("Missing Azure DevOps credentials in .env file.")
    exit(1)

# Build Azure DevOps connection
organization_url = f"https://dev.azure.com/{AZURE_DEVOPS_ORG}"
credentials = BasicAuthentication('', AZURE_DEVOPS_PAT)
connection = Connection(base_url=organization_url, creds=credentials)
wit_client = connection.clients.get_work_item_tracking_client()

# --------------------------------------------
# Set up SQLite database and create tables.
DB_FILE = "historical_data.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

def reset_database(cursor):
    """
    WARNING: This function drops all existing tables in the database.
    Remove or disable this function if you do not want to clear your existing data.
    """
    drop_sql = """
    DROP TABLE IF EXISTS comments;
    DROP TABLE IF EXISTS revisions;
    DROP TABLE IF EXISTS work_item_tags;
    DROP TABLE IF EXISTS work_items;
    DROP TABLE IF EXISTS users;
    """
    cursor.executescript(drop_sql)
    conn.commit()
    logger.info("Database reset: All existing tables dropped.")

def initialize_database(cursor):
    """
    Create the schema matching your updated design including the 'reason' column.
    """
    schema_sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      display_name TEXT,
      url TEXT,
      unique_name TEXT,
      image_url TEXT,
      descriptor TEXT
    );

    CREATE TABLE IF NOT EXISTS work_items (
      id INTEGER PRIMARY KEY,
      work_item_type TEXT,
      title TEXT,
      state TEXT,
      reason TEXT,
      history TEXT,
      created_date TEXT,
      changed_date TEXT,
      comment_count INTEGER,
      team_project TEXT,
      area_path TEXT,
      area_id INTEGER,
      area_level1 TEXT,
      area_level2 TEXT,
      iteration_path TEXT,
      iteration_id INTEGER,
      iteration_level1 TEXT,
      iteration_level2 TEXT,
      iteration_level3 TEXT,
      iteration_level4 TEXT,
      parent INTEGER,
      story_points REAL,
      original_estimate REAL,
      remaining_work REAL,
      completed_work REAL,
      priority INTEGER,
      stack_rank REAL,
      watermark INTEGER,
      person_id INTEGER,
      state_change_date TEXT,
      activated_date TEXT,
      closed_date TEXT,
      custom_work TEXT,
      description TEXT,
      created_by_id TEXT,
      changed_by_id TEXT,
      authorized_as_id TEXT,
      assigned_to_id TEXT,
      extra_fields TEXT
    );

    CREATE TABLE IF NOT EXISTS work_item_tags (
      work_item_id INTEGER,
      tag TEXT,
      PRIMARY KEY (work_item_id, tag),
      FOREIGN KEY(work_item_id) REFERENCES work_items(id)
    );

    CREATE TABLE IF NOT EXISTS revisions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      work_item_id INTEGER,
      rev INTEGER,
      area_id INTEGER,
      node_name TEXT,
      area_level1 TEXT,
      iteration_id INTEGER,
      iteration_level1 TEXT,
      iteration_level2 TEXT,
      iteration_level3 TEXT,
      iteration_level4 TEXT,
      work_item_type TEXT,
      state TEXT,
      reason TEXT,
      assigned_to_id TEXT,
      created_date TEXT,
      created_by_id TEXT,
      changed_date TEXT,
      changed_by_id TEXT,
      authorized_date TEXT,
      revised_date TEXT,
      authorized_as_id TEXT,
      watermark INTEGER,
      comment_count INTEGER,
      team_project TEXT,
      area_path TEXT,
      iteration_path TEXT,
      title TEXT,
      story_points REAL,
      original_estimate REAL,
      remaining_work REAL,
      completed_work REAL,
      closed_date TEXT,
      closed_by_id TEXT,
      priority INTEGER,
      stack_rank REAL,
      FOREIGN KEY(work_item_id) REFERENCES work_items(id)
    );

    CREATE TABLE IF NOT EXISTS comments (
      comment_id INTEGER PRIMARY KEY,
      work_item_id INTEGER,
      rev INTEGER,
      comment_type TEXT,
      state TEXT,
      text TEXT,
      created_date TEXT,
      created_by_id TEXT,
      modified_date TEXT,
      modified_by_id TEXT,
      FOREIGN KEY(work_item_id) REFERENCES work_items(id)
    );
    """
    cursor.executescript(schema_sql)
    conn.commit()
    logger.info("Database schema created/verified.")

# Ensure that our schema exists and is up to date.
reset_database(cursor)
initialize_database(cursor)

def safe_str(val):
    """Convert a value to string if not None, otherwise return None."""
    if val is None:
        return None
    return str(val)

def insert_user(user_obj):
    """
    Insert a user record into the users table if available.
    Returns the unique user id if inserted or existing, otherwise None.
    """
    if not user_obj or not isinstance(user_obj, dict):
        return None
    # Use 'id' if available; fall back on 'uniqueName'
    user_id = safe_str(user_obj.get("id")) or safe_str(user_obj.get("uniqueName"))
    if not user_id:
        return None
    display_name = safe_str(user_obj.get("displayName", ""))
    unique_name = safe_str(user_obj.get("uniqueName", ""))
    url = safe_str(user_obj.get("url", ""))
    image_url = safe_str(user_obj.get("imageUrl", ""))
    descriptor = safe_str(user_obj.get("descriptor", ""))
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO users (id, display_name, url, unique_name, image_url, descriptor)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, display_name, url, unique_name, image_url, descriptor))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to insert user {user_id}: {e}")
    return user_id

def get_comment_attr(item, attr, default=""):
    """
    Helper function that retrieves the attribute 'attr' from the comment.
    Uses .get() if available, otherwise falls back to attribute access.
    """
    if hasattr(item, "get"):
        return item.get(attr, default)
    return getattr(item, attr, default)

def insert_comment(comment, work_item_id):
    """
    Insert a comment using the updated schema.
    Uses correct columns: created_by_id and modified_by_id.
    Supports comment objects as dictionaries or objects with dot attributes.
    """
    comment_id     = get_comment_attr(comment, "id")
    rev            = get_comment_attr(comment, "rev")
    comment_type   = get_comment_attr(comment, "commentType", "")
    state          = get_comment_attr(comment, "state", "")
    text           = get_comment_attr(comment, "text", "")
    created_date   = get_comment_attr(comment, "createdDate", "")
    created_by_obj = get_comment_attr(comment, "createdBy", {})
    modified_date  = get_comment_attr(comment, "modifiedDate", "")
    modified_by_obj= get_comment_attr(comment, "modifiedBy", {})

    created_by_id  = insert_user(created_by_obj)
    modified_by_id = insert_user(modified_by_obj)

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO comments
            (comment_id, work_item_id, rev, comment_type, state, text, created_date, created_by_id, modified_date, modified_by_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comment_id,
            work_item_id,
            rev,
            comment_type,
            state,
            text,
            created_date,
            created_by_id,
            modified_date,
            modified_by_id
        ))
        conn.commit()
        logger.info(f"Inserted comment {comment_id} for work item {work_item_id}.")
    except Exception as e:
        logger.error(f"Error inserting comment {comment_id} for work item {work_item_id}: {e}")

# --------------------------------------------
# Define a WIQL query to fetch work items.
wiql_query = f"""
SELECT [System.Id], 
       [System.Title],
       [System.WorkItemType],
       [System.State],
       [System.Reason],
       [System.History],
       [System.CreatedDate],
       [System.CreatedBy],
       [System.ChangedDate],
       [System.ChangedBy],
       [System.AssignedTo],
       [System.TeamProject],
       [System.AreaPath],
       [System.IterationPath],
       [System.Parent],
       [System.CommentCount],
       [Microsoft.VSTS.Scheduling.StoryPoints],
       [Microsoft.VSTS.Scheduling.OriginalEstimate],
       [Microsoft.VSTS.Scheduling.RemainingWork],
       [Microsoft.VSTS.Common.Priority],
       [Microsoft.VSTS.Common.StackRank],
       [System.Watermark],
       [System.Tags]
FROM WorkItems
WHERE [System.TeamProject] = '{AZURE_DEVOPS_PROJECT}'
ORDER BY [System.CreatedDate] DESC
"""

logger.info("Executing WIQL query to fetch work items...")
query_results = wit_client.query_by_wiql({"query": wiql_query})
work_item_refs = query_results.work_items

if not work_item_refs:
    logger.info("No work items found.")
else:
    # Replace individual work item fetching with bulk retrieval
    all_ids = [item.id for item in work_item_refs]
    CHUNK_SIZE = 200  # Max allowed by Azure DevOps API

    for i in range(0, len(all_ids), CHUNK_SIZE):
        chunk_ids = all_ids[i:i+CHUNK_SIZE]
        work_items = wit_client.get_work_items(ids=chunk_ids, expand="All")
        
        # Process all items in this chunk
        for work_item in work_items:
            try:
                # Fetch complete details for this work item.
                work_item = wit_client.get_work_item(work_item.id, expand="All")
                fields = work_item.fields
                work_item_id = work_item.id
                work_item_type = fields.get("System.WorkItemType", "")
                title = fields.get("System.Title", "")
                state = fields.get("System.State", "")
                reason = fields.get("System.Reason", "")
                history = fields.get("System.History", "")
                created_date = fields.get("System.CreatedDate", "")
                changed_date = fields.get("System.ChangedDate", "")
                comment_count = fields.get("System.CommentCount", 0)
                team_project = fields.get("System.TeamProject", "")
                area_path = fields.get("System.AreaPath", "")
                iteration_path = fields.get("System.IterationPath", "")
                parent = fields.get("System.Parent", None)
                story_points = fields.get("Microsoft.VSTS.Scheduling.StoryPoints", None)
                original_estimate = fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", None)
                remaining_work = fields.get("Microsoft.VSTS.Scheduling.RemainingWork", None)
                priority = fields.get("Microsoft.VSTS.Common.Priority", None)
                stack_rank = fields.get("Microsoft.VSTS.Common.StackRank", None)
                watermark = fields.get("System.Watermark", None)

                # Process user objects; these may be dicts.
                created_by_obj = fields.get("System.CreatedBy", {})
                changed_by_obj = fields.get("System.ChangedBy", {})
                assigned_to_obj = fields.get("System.AssignedTo", {})
                authorized_as_obj = fields.get("System.AuthorizedAs", {})

                created_by_id = insert_user(created_by_obj)
                changed_by_id = insert_user(changed_by_obj)
                assigned_to_id = insert_user(assigned_to_obj)
                authorized_as_id = insert_user(authorized_as_obj)

                extra_fields = json.dumps(fields)

                cursor.execute("""
                    INSERT OR REPLACE INTO work_items
                    (id, work_item_type, title, state, reason, history, created_date, changed_date, 
                     comment_count, team_project, area_path, area_id, area_level1, area_level2,
                     iteration_path, iteration_id, iteration_level1, iteration_level2, iteration_level3,
                     iteration_level4, parent, story_points, original_estimate, remaining_work, completed_work,
                     priority, stack_rank, watermark, person_id, state_change_date, activated_date,
                     closed_date, custom_work, description, created_by_id, changed_by_id, authorized_as_id,
                     assigned_to_id, extra_fields)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    work_item_id,
                    work_item_type,
                    title,
                    state,
                    reason,
                    history,
                    created_date,
                    changed_date,
                    comment_count,
                    team_project,
                    fields.get("System.AreaPath"),
                    fields.get("System.AreaId"),
                    fields.get("System.AreaLevel1"),
                    fields.get("System.AreaLevel2"),
                    fields.get("System.IterationPath"),
                    fields.get("System.IterationId"),
                    fields.get("System.IterationLevel1"),
                    fields.get("System.IterationLevel2"),
                    fields.get("System.IterationLevel3"),
                    fields.get("System.IterationLevel4"),
                    parent,
                    story_points,
                    original_estimate,
                    remaining_work,
                    fields.get("Microsoft.VSTS.Scheduling.CompletedWork"),
                    priority,
                    stack_rank,
                    watermark,
                    fields.get("System.PersonId"),
                    fields.get("Microsoft.VSTS.Common.StateChangeDate"),
                    fields.get("Microsoft.VSTS.Common.ActivatedDate"),
                    fields.get("Microsoft.VSTS.Common.ClosedDate"),
                    fields.get("Custom.Work"),
                    fields.get("System.Description"),
                    created_by_id,
                    changed_by_id,
                    authorized_as_id,
                    assigned_to_id,
                    extra_fields
                ))
                conn.commit()
                logger.info(f"Inserted work item {work_item_id} (Created: {created_date}).")

                # Process and insert tags into the work_item_tags table.
                tags_field = fields.get("System.Tags", "")
                if tags_field:
                    tags = [tag.strip() for tag in tags_field.split(";") if tag.strip()]
                    for tag in tags:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO work_item_tags (work_item_id, tag)
                                VALUES (?, ?)
                            """, (work_item_id, tag))
                        except Exception as tag_err:
                            logger.error(f"Error inserting tag '{tag}' for work item {work_item_id}: {tag_err}")
                    conn.commit()

                # --------------------------------------------
                # Fetch and insert all revisions for the work item.
                revisions = wit_client.get_revisions(work_item_id, expand="All")
                if revisions:
                    for rev in revisions:
                        rev_num = getattr(rev, "rev", None)
                        rev_changed_date = rev.fields.get("System.ChangedDate", "")
                        rev_state = rev.fields.get("System.State", "")
                        cursor.execute("""
                            INSERT INTO revisions (work_item_id, rev, changed_date, state)
                            VALUES (?, ?, ?, ?)
                        """, (work_item_id, rev_num, rev_changed_date, rev_state))
                    conn.commit()
                    logger.info(f"Inserted {len(revisions)} revisions for work item {work_item_id}.")
                else:
                    logger.info(f"No revisions found for work item {work_item_id}.")

                # --------------------------------------------
                # Fetch and insert important comments for the work item.
                try:
                    comments_response = wit_client.get_comments(
                        project=AZURE_DEVOPS_PROJECT, 
                        work_item_id=work_item_id
                    )
                    if comments_response and comments_response.comments:
                        for comment in comments_response.comments:
                            insert_comment(comment, work_item_id)
                    else:
                        logger.info(f"No comments for work item {work_item_id}.")
                except Exception as e:
                    logger.error(f"Error fetching comments for work item {work_item_id}: {e}")

            except Exception as e:
                logger.error(f"Error processing work item {work_item.id}: {e}")

    # Final commit for remaining items
    conn.commit()
    logger.info("Data fetch and insert complete.")

conn.close() 