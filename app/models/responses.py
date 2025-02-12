from typing import Dict, List
from pydantic import BaseModel
from app.models.ticket import Ticket

class TicketMetadata(BaseModel):
    total_count: int
    type_counts: Dict[str, int]
    state_counts: Dict[str, int]

class TicketResponse(BaseModel):
    metadata: TicketMetadata
    tickets: List[Ticket] 