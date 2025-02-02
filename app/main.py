from fastapi import FastAPI
from app.api.endpoints import tickets
from app.core.config import settings

app = FastAPI(
    title="Azure DevOps Ticket Scraper",
    description="API service for scraping and analyzing Azure DevOps tickets",
    version="1.0.0"
)

app.include_router(tickets.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Azure DevOps Ticket Scraper API"} 