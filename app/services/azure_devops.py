import logging
from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication
from msrest.authentication import BasicAuthentication
from app.core.config import settings
from app.models.ticket import Ticket
from fastapi import HTTPException
from app.models.responses import TicketResponse, TicketMetadata
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureDevOpsService:
    def __init__(self):
        try:
            organization_url = f"https://dev.azure.com/{settings.AZURE_DEVOPS_ORG}"
            logger.info(f"Initializing Azure DevOps connection to: {organization_url}")
            
            credentials = BasicAuthentication('', settings.AZURE_DEVOPS_PAT)
            self.connection = Connection(
                base_url=organization_url,
                creds=credentials
            )
            
            self.client = self.connection.clients.get_work_item_tracking_client()
            logger.info("Successfully initialized Azure DevOps client")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure DevOps connection: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Azure DevOps connection failed: {str(e)}"
            )

    async def get_tickets(self, query: str = "") -> TicketResponse:
        try:
            logger.info(f"Executing WIQL query: {query}")
            
            wiql = {
                "query": query if query else """
                    SELECT [System.Id], 
                           [System.Title], 
                           [System.WorkItemType], 
                           [System.State],
                           [System.AreaPath],
                           [System.IterationPath],
                           [Microsoft.VSTS.Common.Priority],
                           [Microsoft.VSTS.Scheduling.StoryPoints],
                           [Microsoft.VSTS.Scheduling.TargetDate],
                           [Microsoft.VSTS.Common.ClosedDate],
                           [Microsoft.VSTS.Scheduling.OriginalEstimate],
                           [Microsoft.VSTS.Scheduling.RemainingWork],
                           [Microsoft.VSTS.Scheduling.CompletedWork],
                           [System.Environment],
                           [Microsoft.VSTS.Common.RootCause],
                           [System.Tags],
                           [System.CreatedDate],
                           [System.ChangedDate],
                           [System.AssignedTo],
                           [System.Description]
                    FROM WorkItems 
                    ORDER BY [System.ChangedDate] DESC
                """
            }
            
            # Execute the query
            logger.debug("Executing WIQL query...")
            wiql_results = self.client.query_by_wiql(wiql).work_items
            
            if not wiql_results:
                logger.info("No work items found")
                return TicketResponse(
                    metadata=TicketMetadata(
                        total_count=0,
                        type_counts={},
                        state_counts={}
                    ),
                    tickets=[]
                )
                
            logger.info(f"Found {len(wiql_results)} work items")
            
            # Get full work items
            tickets = []
            for result in wiql_results:
                try:
                    work_item = self.client.get_work_item(
                        result.id,
                        expand="All"
                    )
                    
                    ticket = Ticket(
                        id=work_item.id,
                        title=work_item.fields.get("System.Title", "No Title"),
                        work_item_type=work_item.fields.get("System.WorkItemType", "Unknown"),
                        state=work_item.fields.get("System.State", "Unknown"),
                        area_path=work_item.fields.get("System.AreaPath"),
                        iteration_path=work_item.fields.get("System.IterationPath"),
                        priority=work_item.fields.get("Microsoft.VSTS.Common.Priority"),
                        priority_text=f"{work_item.fields.get('Microsoft.VSTS.Common.Priority', '')} - {work_item.fields.get('Microsoft.VSTS.Common.PriorityName', '')}",
                        story_points=work_item.fields.get("Microsoft.VSTS.Scheduling.StoryPoints"),
                        target_date=work_item.fields.get("Microsoft.VSTS.Scheduling.TargetDate"),
                        prod_release_date=work_item.fields.get("Microsoft.VSTS.Common.ClosedDate"),
                        actual_release_date=work_item.fields.get("Microsoft.VSTS.Common.ResolvedDate"),
                        original_estimate=work_item.fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate"),
                        remaining_work=work_item.fields.get("Microsoft.VSTS.Scheduling.RemainingWork"),
                        completed_work=work_item.fields.get("Microsoft.VSTS.Scheduling.CompletedWork"),
                        environment=work_item.fields.get("System.Environment"),
                        root_cause=work_item.fields.get("Microsoft.VSTS.Common.RootCause"),
                        found_in_environment=work_item.fields.get("Microsoft.VSTS.TCM.TestEnvironment"),
                        created_date=work_item.fields.get("System.CreatedDate"),
                        updated_date=work_item.fields.get("System.ChangedDate"),
                        assigned_to=work_item.fields.get("System.AssignedTo", {}).get("displayName"),
                        description=work_item.fields.get("System.Description", ""),
                        tags=work_item.fields.get("System.Tags", "").split(";") if work_item.fields.get("System.Tags") else [],
                        requested_by=work_item.fields.get("System.CreatedBy", {}).get("displayName"),
                        facility=work_item.fields.get("Custom.MROFacility")  # Adjust field name if different
                    )
                    tickets.append(ticket)
                    
                except Exception as e:
                    logger.error(f"Error processing work item {result.id}: {str(e)}")
                    continue
                
            # Calculate metadata
            type_counts = Counter(ticket.work_item_type for ticket in tickets)
            state_counts = Counter(ticket.state for ticket in tickets)
            
            metadata = TicketMetadata(
                total_count=len(tickets),
                type_counts=dict(type_counts),
                state_counts=dict(state_counts)
            )
            
            return TicketResponse(
                metadata=metadata,
                tickets=tickets
            )
            
        except Exception as e:
            logger.error(f"Error fetching tickets: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch tickets: {str(e)}"
            ) 