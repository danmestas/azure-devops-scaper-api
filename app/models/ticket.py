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