import os
import logging
from pprint import pprint
import json

# To load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(".env")

from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication
from msrest.authentication import BasicAuthentication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
AZURE_DEVOPS_ORG = os.getenv("AZURE_DEVOPS_ORG")
AZURE_DEVOPS_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT")

if not (AZURE_DEVOPS_ORG and AZURE_DEVOPS_PROJECT and AZURE_DEVOPS_PAT):
    logger.error("Missing Azure DevOps credentials. Please configure AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_PAT in your .env file.")
    exit(1)

# Build the organization URL
organization_url = f"https://dev.azure.com/{AZURE_DEVOPS_ORG}"
logger.info(f"Connecting to Azure DevOps at {organization_url}")

# Create credentials using PAT
credentials = BasicAuthentication('', AZURE_DEVOPS_PAT)
connection = Connection(base_url=organization_url, creds=credentials)

# Get the Work Item Tracking client
wit_client = connection.clients.get_work_item_tracking_client()

# Construct WIQL query with fields per the current REST API documentation.
wiql_query = f"""
SELECT 
  [System.Id],
  [System.WorkItemType],
  [System.Title],
  [System.State],
  [System.Reason],
  [System.CreatedDate],
  [System.CreatedBy],
  [System.ChangedDate],
  [System.ChangedBy],
  [System.AssignedTo],
  [System.AreaPath],
  [System.IterationPath],
  [System.Tags],
  [Microsoft.VSTS.Common.Priority],
  [Microsoft.VSTS.Common.StackRank]
FROM WorkItems
WHERE [System.TeamProject] = '{AZURE_DEVOPS_PROJECT}'
ORDER BY [System.ChangedDate] DESC
"""

logger.info("Executing WIQL query to fetch work items.")
query_results = wit_client.query_by_wiql({"query": wiql_query})

work_items = query_results.work_items

if not work_items:
    logger.info("No work items found.")
else:
    logger.info(f"Retrieved {len(work_items)} work items.")
    for item in work_items:
        try:
            # Expand all details of the work item (fields, relations, etc.)
            work_item = wit_client.get_work_item(item.id, expand="All")
            
            print("=" * 80)
            print(f"Work Item ID: {work_item.id}")
            print(f"Title: {work_item.fields.get('System.Title')}")
            print(f"State: {work_item.fields.get('System.State')}\n")
            
            print("All available fields:")
            pprint(work_item.fields)
            print("\nRelations:")
            # Relations (attachments, links, etc.) appear in the 'relations' key.
            relations = work_item.fields.get("relations", [])
            if relations:
                for relation in relations:
                    print(f"  - Relationship: {relation.get('rel')}")
                    print(f"    URL: {relation.get('url')}")
                    print("    Attributes:")
                    pprint(relation.get("attributes", {}))
                    print("-" * 40)
            else:
                print("No relations found.")
            
            # Fetch and print only the important comment information for the work item.
            try:
                comments_response = wit_client.get_comments(
                    project=AZURE_DEVOPS_PROJECT,
                    work_item_id=work_item.id
                )

                if comments_response and comments_response.comments:
                    print("\nImportant Comment Data:")
                    for comment in comments_response.comments:
                        # Extract essential fields
                        comment_id = getattr(comment, "id", "Unknown")
                        created_date = getattr(comment, "created_date", "Unknown")
                        text = getattr(comment, "text", "").strip()

                        # Extract created_by details safely.
                        created_by_obj = getattr(comment, "created_by", None)
                        if created_by_obj:
                            if isinstance(created_by_obj, dict):
                                created_by = created_by_obj.get("displayName", "Unknown")
                            else:
                                created_by = getattr(created_by_obj, "display_name", "Unknown")
                        else:
                            created_by = "Unknown"

                        # Print the important comment details.
                        print(f"Comment ID: {comment_id}")
                        print(f"Created Date: {created_date}")
                        print(f"Created By: {created_by}")
                        print(f"Text: {text}")
                        print("-" * 40)
                else:
                    print("No comments for this work item.")
            except Exception as e:
                logger.error(f"Error retrieving comments for work item {work_item.id}: {e}")
            
            # -----------------------------
            # NEW: Fetch and print ALL revisions for the work item.
            try:
                revisions = wit_client.get_revisions(work_item.id, expand="All")
                if revisions:
                    print("\nAll Revisions:")
                    for rev in revisions:
                        rev_num = getattr(rev, "rev", "Unknown")
                        changed_date = rev.fields.get("System.ChangedDate", "Unknown")
                        print("=" * 60)
                        print(f"Revision {rev_num} - Changed Date: {changed_date}")
                        print("Fields:")
                        for field_name, field_value in rev.fields.items():
                            # Print each field and its value.
                            print(f"  {field_name}: {field_value}")
                        print("=" * 60)
                else:
                    print("No revisions found for this work item.")
            except Exception as e:
                logger.error(f"Error fetching revisions for work item {work_item.id}: {e}")
            
            print("=" * 80 + "\n")
        except Exception as e:
            logger.error(f"Error fetching work item {item.id}: {e}") 