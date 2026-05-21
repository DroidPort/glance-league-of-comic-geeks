from typing import Annotated
from fastapi import APIRouter, Depends

from API_Endpoints.helpers.models import GetPullListRequest, PullListEntry
from API_Endpoints.helpers.service import LeagueOfComicGeeksService
from API_Endpoints.dependencies import get_service

router = APIRouter()


@router.get("", response_model=list[PullListEntry])
async def pull_list(
    service: Annotated[LeagueOfComicGeeksService, Depends(get_service)],
    user_id: str,
) -> list[PullListEntry]:
    """Get the user's comic pull list."""
    get_pull_list_request = GetPullListRequest(user_id=user_id)
    return await service.get_pull_list(request=get_pull_list_request)