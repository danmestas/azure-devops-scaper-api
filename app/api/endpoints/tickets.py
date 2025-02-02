from fastapi import APIRouter, Query
from typing import List
from app.services.azure_devops import AzureDevOpsService
from app.models.ticket import Ticket

router = APIRouter()
azure_service = AzureDevOpsService()

@router.get("/tickets", response_model=List[Ticket])
async def get_tickets(query: str = Query(None, description="Custom WIQL query")):
    """
    Retrieve tickets from Azure DevOps.
    Optionally provide a custom WIQL query.
    """
    return await azure_service.get_tickets(query) 