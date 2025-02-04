from fastapi import APIRouter, Query
from typing import List, Optional
from enum import Enum
from datetime import datetime
from app.services.azure_devops import AzureDevOpsService
from app.models.ticket import Ticket

router = APIRouter()
azure_service = AzureDevOpsService()

class WorkItemType(str, Enum):
    BUG = "Bug"
    USER_STORY = "User Story"
    TASK = "Task"
    FEATURE = "Feature"
    EPIC = "Epic"

class State(str, Enum):
    NEW = "New"
    ACTIVE = "Active"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

@router.get("/tickets", response_model=List[Ticket])
async def get_tickets(
    work_item_type: Optional[WorkItemType] = None,
    state: Optional[State] = None,
    assigned_to: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    modified_after: Optional[datetime] = None,
    priority: Optional[int] = Query(None, ge=1, le=4),
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    raw_query: Optional[str] = Query(None, description="Raw WIQL query for advanced users")
):
    """
    Get tickets with flexible filtering options.
    
    - **work_item_type**: Filter by type (Bug, User Story, etc.)
    - **state**: Filter by state (New, Active, etc.)
    - **assigned_to**: Filter by assignee email or name
    - **tags**: Filter by tags (comma-separated)
    - **modified_after**: Get items modified after this date
    - **priority**: Filter by priority (1-4)
    - **search**: Search in title and description
    - **limit**: Maximum number of results
    - **raw_query**: Advanced: Use raw WIQL query
    """
    if raw_query:
        return await azure_service.get_tickets(raw_query)

    # Build WIQL query from parameters
    conditions = []
    
    if work_item_type:
        conditions.append(f"[System.WorkItemType] = '{work_item_type}'")
    
    if state:
        conditions.append(f"[System.State] = '{state}'")
    
    if assigned_to:
        conditions.append(f"[System.AssignedTo] = '{assigned_to}'")
    
    if tags:
        tag_conditions = [f"[System.Tags] CONTAINS '{tag.strip()}'" 
                         for tag in tags.split(',')]
        conditions.append(f"({' OR '.join(tag_conditions)})")
    
    if modified_after:
        conditions.append(
            f"[System.ChangedDate] >= '{modified_after.isoformat()}'"
        )
    
    if priority:
        conditions.append(f"[Microsoft.VSTS.Common.Priority] = {priority}")
    
    if search:
        conditions.append(
            f"(CONTAINS([System.Title], '{search}') OR "
            f"CONTAINS([System.Description], '{search}'))"
        )

    where_clause = " AND ".join(conditions) if conditions else "1 = 1"
    
    query = f"""
        SELECT [System.Id], 
               [System.Title], 
               [System.WorkItemType], 
               [System.State],
               [System.AssignedTo],
               [System.Tags],
               [System.CreatedDate],
               [System.ChangedDate],
               [System.Description]
        FROM WorkItems 
        WHERE {where_clause}
        ORDER BY [System.ChangedDate] DESC
    """

    return await azure_service.get_tickets(query)

# Add additional endpoints for common queries
@router.get("/tickets/my-tasks", response_model=List[Ticket])
async def get_my_tasks():
    """Get all tasks assigned to the authenticated user"""
    query = """
        SELECT [System.Id], [System.Title]
        FROM WorkItems 
        WHERE [System.AssignedTo] = @Me 
        AND [System.WorkItemType] = 'Task'
        ORDER BY [System.ChangedDate] DESC
    """
    return await azure_service.get_tickets(query)

@router.get("/tickets/blocked", response_model=List[Ticket])
async def get_blocked_items():
    """Get all blocked items"""
    query = """
        SELECT [System.Id], [System.Title]
        FROM WorkItems 
        WHERE [System.Tags] CONTAINS 'Blocked'
        AND [System.State] <> 'Closed'
    """
    return await azure_service.get_tickets(query) 