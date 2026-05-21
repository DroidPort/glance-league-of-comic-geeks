from typing import Annotated
import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from API_Endpoints.helpers.models import GetPullListRequest, PullListEntry, NewRelease
from API_Endpoints.helpers.service import LeagueOfComicGeeksService
from API_Endpoints.dependencies import get_service

router = APIRouter()


class PullListPlusPopularResponse(BaseModel):
    my_pulls: list[PullListEntry]
    popular: list[NewRelease]


@router.get("", response_model=PullListPlusPopularResponse)
async def pull_list_plus_popular(
    service: Annotated[LeagueOfComicGeeksService, Depends(get_service)],
    user_id: str,
    popular_limit: int = 30,
) -> PullListPlusPopularResponse:
    """
    Returns the user's weekly pull list alongside popular new releases for next week,
    with any pull list titles already filtered out of the popular list.
    """
    get_pull_list_request = GetPullListRequest(user_id=user_id)
    my_pulls, all_popular = await asyncio.gather(
        service.get_pull_list(request=get_pull_list_request),
        service.get_next_week_releases(limit=100),
    )

    # Build a set of normalised titles from the pull list for O(1) lookup
    pull_titles = {entry.title.strip().lower() for entry in my_pulls}

    # Filter popular list — exclude anything already in the pull list
    popular_filtered = [
        r for r in all_popular if r.title.strip().lower() not in pull_titles
    ][:popular_limit]

    return PullListPlusPopularResponse(my_pulls=my_pulls, popular=popular_filtered)