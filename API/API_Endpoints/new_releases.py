from typing import Annotated
from fastapi import APIRouter, Depends

from API_Endpoints.helpers.models import NewRelease
from API_Endpoints.helpers.service import LeagueOfComicGeeksService
from API_Endpoints.dependencies import get_service

router = APIRouter()


@router.get("", response_model=list[NewRelease])
async def new_releases(
    service: Annotated[LeagueOfComicGeeksService, Depends(get_service)],
    limit: int = 20,
) -> list[NewRelease]:
    """Get new comic releases."""
    return await service.get_new_releases(limit=limit)