from typing import Annotated
from fastapi import APIRouter, Depends

from API_Endpoints.helpers.models import DiscoveryResponse
from API_Endpoints.helpers.service import LeagueOfComicGeeksService
from API_Endpoints.dependencies import get_service

router = APIRouter()


@router.get("", response_model=DiscoveryResponse)
async def discovery(
    service: Annotated[LeagueOfComicGeeksService, Depends(get_service)],
) -> DiscoveryResponse:
    """Get discovery content (popular, community picks, indie picks)."""
    return await service.get_discovery()