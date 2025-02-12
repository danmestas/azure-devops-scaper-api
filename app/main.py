import sys
import logging

if sys.version_info < (3, 10):
    raise RuntimeError("This application requires Python 3.10 or higher")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import tickets
from app.core.config import settings
from app.services.azure_devops import AzureDevOpsService
from app.api.endpoints.tickets import sprint_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
app.include_router(sprint_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Azure DevOps Ticket Scraper API"}

@app.get("/health")
async def health_check():
    try:
        logger.info("Performing health check...")
        azure_service = AzureDevOpsService()
        
        # Try to get one ticket to verify connection
        logger.info("Testing Azure DevOps connection...")
        await azure_service.get_tickets("SELECT TOP 1 [System.Id] FROM WorkItems")
        
        logger.info("Health check successful")
        return {
            "status": "healthy",
            "azure_devops": "connected",
            "organization": settings.AZURE_DEVOPS_ORG,
            "project": settings.AZURE_DEVOPS_PROJECT
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "organization": settings.AZURE_DEVOPS_ORG,
            "project": settings.AZURE_DEVOPS_PROJECT
        }

# Add error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error occurred: {exc.detail}")
    return {"status": "error", "message": exc.detail}

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error occurred: {str(exc)}", exc_info=True)
    return {"status": "error", "message": "Internal server error"} 