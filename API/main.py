from fastapi import FastAPI
import asyncio

from API_Endpoints.pull_list import router as pull_list_router
from API_Endpoints.discovery import router as discovery_router
from API_Endpoints.solicitations import router as solicitations_router
from API_Endpoints.new_releases import router as new_releases_router
from API_Endpoints.pull_list_plus_popular import router as pull_list_plus_popular_router
from API_Endpoints.dependencies import get_service
from API_Endpoints.helpers.service import _get_async_client

app = FastAPI()


@app.on_event("startup")
async def startup():
    """Pre-warm the cache on startup."""
    service = get_service()
    asyncio.create_task(service.get_discovery())
    asyncio.create_task(service.get_new_releases())
    asyncio.create_task(service.get_solicitations())


@app.on_event("shutdown")
async def shutdown():
    """Close the async HTTP client on shutdown."""
    client = _get_async_client()
    await client.aclose()


# Include all routers
app.include_router(pull_list_router, prefix="/pull-list")
app.include_router(discovery_router, prefix="/discovery")
app.include_router(solicitations_router, prefix="/solicitations")
app.include_router(new_releases_router, prefix="/new-releases")
app.include_router(pull_list_plus_popular_router, prefix="/pull-list-plus-popular")