from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Azure DevOps Settings
    AZURE_DEVOPS_ORG: str
    AZURE_DEVOPS_PROJECT: str
    AZURE_DEVOPS_PAT: str

    # Server Settings
    SERVER_PORT: int = 8000

    # Default WIQL Query
    DEFAULT_WIQL: str = """
        SELECT [System.Id], 
               [System.Title], 
               [System.WorkItemType], 
               [System.State] 
        FROM WorkItems 
        ORDER BY [System.ChangedDate] DESC
    """

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Azure DevOps Intelligence Engine"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = """
    🚀 Enterprise-Grade Azure DevOps Intelligence Platform. 
    Transform your ticket chaos into actionable insights.
    """

    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False  # This allows both server_port and SERVER_PORT to work

settings = Settings() 