from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from API_Endpoints.helpers.models import SolicitationCard, SolicitationMonth
from API_Endpoints.helpers.service import LeagueOfComicGeeksService
from API_Endpoints.dependencies import get_service

router = APIRouter()


@router.get("", response_model=list[SolicitationCard])
async def solicitations(
    service: Annotated[LeagueOfComicGeeksService, Depends(get_service)],
) -> list[SolicitationCard]:
    """Get upcoming comic solicitations as a flat list."""
    return await service.get_solicitations()


@router.get("/grouped", response_model=list[SolicitationMonth])
async def solicitations_grouped(
    service: Annotated[LeagueOfComicGeeksService, Depends(get_service)],
    exclude: str = "",
) -> list[SolicitationMonth]:
    """Get upcoming comic solicitations grouped by month."""
    exclude_list = [p.strip() for p in exclude.split(",") if p.strip()] if exclude else []
    return await service.get_solicitations_grouped(exclude=exclude_list)


@router.get("/debug", response_class=HTMLResponse)
async def debug_solicitations(
    service: Annotated[LeagueOfComicGeeksService, Depends(get_service)],
):
    """Returns the raw HTML from LoCG solicitations page for debugging."""
    html = await service.fetch_solicitations_html()
    return html