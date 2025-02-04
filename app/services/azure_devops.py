from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication
from msrest.authentication import BasicAuthentication
from app.core.config import settings
from app.models.ticket import Ticket

class AzureDevOpsService:
    def __init__(self):
        # Create the connection URL correctly
        organization_url = f"https://dev.azure.com/{settings.AZURE_DEVOPS_ORG}"
        
        # Create credentials with PAT
        credentials = BasicAuthentication('', settings.AZURE_DEVOPS_PAT)
        
        # Initialize the connection
        self.connection = Connection(
            base_url=organization_url,
            creds=credentials
        )
        
        # Get the client
        self.client = self.connection.clients.get_work_item_tracking_client()

    async def get_tickets(self, query: str = ""):
        try:
            wiql = {
                "query": query if query else """
                    SELECT [System.Id], 
                           [System.Title], 
                           [System.WorkItemType], 
                           [System.State] 
                    FROM WorkItems 
                    ORDER BY [System.ChangedDate] DESC
                """
            }
            
            # Execute the query
            wiql_results = self.client.query_by_wiql(wiql).work_items
            
            if not wiql_results:
                return []
                
            # Get full work items
            tickets = []
            for result in wiql_results:
                work_item = self.client.get_work_item(
                    result.id,
                    expand="All"  # Get all fields
                )
                
                ticket = Ticket(
                    id=work_item.id,
                    title=work_item.fields["System.Title"],
                    work_item_type=work_item.fields["System.WorkItemType"],
                    state=work_item.fields["System.State"],
                    created_date=work_item.fields["System.CreatedDate"],
                    updated_date=work_item.fields["System.ChangedDate"],
                    assigned_to=work_item.fields.get("System.AssignedTo", {}).get("displayName"),
                    description=work_item.fields.get("System.Description", ""),
                    tags=work_item.fields.get("System.Tags", "").split(";") if work_item.fields.get("System.Tags") else []
                )
                tickets.append(ticket)
                
            return tickets
            
        except Exception as e:
            print(f"Error fetching tickets: {str(e)}")
            raise 