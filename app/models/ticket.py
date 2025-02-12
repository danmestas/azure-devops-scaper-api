from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Ticket(BaseModel):
    id: int
    title: str
    work_item_type: str
    state: str
    created_date: datetime
    updated_date: datetime
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    
    # New fields from the work item
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    priority: Optional[int] = None
    priority_text: Optional[str] = None  # e.g., "2 - Critical"
    story_points: Optional[int] = None
    target_date: Optional[datetime] = None
    prod_release_date: Optional[datetime] = None
    actual_release_date: Optional[datetime] = None
    
    # Effort tracking
    original_estimate: Optional[float] = None
    remaining_work: Optional[float] = None
    completed_work: Optional[float] = None
    
    # Additional fields
    environment: Optional[str] = None
    root_cause: Optional[str] = None
    found_in_environment: Optional[str] = None
    requested_by: Optional[str] = None
    facility: Optional[str] = None 