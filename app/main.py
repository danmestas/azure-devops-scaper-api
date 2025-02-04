import sys

if sys.version_info < (3, 10):
    raise RuntimeError("This application requires Python 3.10 or higher")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import tickets
from app.core.config import settings
from app.services.azure_devops import AzureDevOpsService

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Azure DevOps Ticket Scraper API"}

@app.get("/health")
async def health_check():
    try:
        azure_service = AzureDevOpsService()
        # Try to get one ticket to verify connection
        await azure_service.get_tickets("SELECT TOP 1 [System.Id] FROM WorkItems")
        return {"status": "healthy", "azure_devops": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)} 