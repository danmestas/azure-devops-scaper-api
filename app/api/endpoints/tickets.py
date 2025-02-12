from fastapi import APIRouter, Query, HTTPException, Path
from typing import List, Optional
from enum import Enum
from datetime import datetime
from app.services.azure_devops import AzureDevOpsService
from app.models.ticket import Ticket
from app.models.responses import TicketResponse

router = APIRouter()
azure_service = AzureDevOpsService()

# Add new router for sprint-related endpoints
sprint_router = APIRouter(prefix="/sprint", tags=["Sprint Management"])

# Default iteration path
DEFAULT_SPRINT_PATH = "Concourse\\Digital MRO\\PI03\\DM-PI03-3"

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

@router.get("/tickets", response_model=TicketResponse)
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
@router.get("/tickets/my-tasks", response_model=TicketResponse)
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

@router.get("/tickets/blocked", response_model=TicketResponse)
async def get_blocked_items():
    """Get all blocked items"""
    query = """
        SELECT [System.Id], [System.Title]
        FROM WorkItems 
        WHERE [System.Tags] CONTAINS 'Blocked'
        AND [System.State] <> 'Closed'
    """
    return await azure_service.get_tickets(query)

@sprint_router.get("/current", response_model=TicketResponse)
async def get_current_sprint_items(
    iteration_path: str = Query(
        default=DEFAULT_SPRINT_PATH,
        description="Sprint iteration path (e.g., 'Concourse\\Digital MRO\\PI03\\DM-PI03-3')"
    )
):
    """Get all items in specified sprint"""
    query = f"""
        SELECT [System.Id], 
               [System.Title], 
               [System.WorkItemType],
               [System.State],
               [System.AssignedTo],
               [System.Tags]
        FROM WorkItems 
        WHERE [System.IterationPath] = '{iteration_path}'
        ORDER BY [System.ChangedDate] DESC
    """
    return await azure_service.get_tickets(query)

@sprint_router.get("/backlog", response_model=TicketResponse)
async def get_sprint_backlog(
    iteration_path: str = Query(
        default=DEFAULT_SPRINT_PATH,
        description="Sprint iteration path (e.g., 'Concourse\\Digital MRO\\PI03\\DM-PI03-3')"
    )
):
    """Get backlog items (unassigned or new) in specified sprint"""
    query = f"""
        SELECT [System.Id], 
               [System.Title], 
               [System.WorkItemType],
               [System.State],
               [System.AssignedTo],
               [System.Tags],
               [Microsoft.VSTS.Common.Priority],
               [System.CreatedDate]
        FROM WorkItems 
        WHERE [System.IterationPath] = '{iteration_path}'
        AND (
            [System.State] = 'New' 
            OR [System.AssignedTo] = ''
            OR [System.AssignedTo] IS NULL
        )
        ORDER BY [Microsoft.VSTS.Common.Priority] ASC,
                 [System.CreatedDate] ASC
    """
    return await azure_service.get_tickets(query)

@sprint_router.get("/blocked", response_model=TicketResponse)
async def get_blocked_in_sprint(
    iteration_path: str = Query(
        default=DEFAULT_SPRINT_PATH,
        description="Sprint iteration path (e.g., 'Concourse\\Digital MRO\\PI03\\DM-PI03-3')"
    )
):
    """Get blocked items in specified sprint"""
    query = f"""
        SELECT [System.Id], 
               [System.Title], 
               [System.WorkItemType],
               [System.State]
        FROM WorkItems 
        WHERE [System.IterationPath] = '{iteration_path}'
        AND [System.Tags] CONTAINS 'Blocked'
        AND [System.State] <> 'Closed'
    """
    return await azure_service.get_tickets(query) 